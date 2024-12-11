import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import re

# ワーカー情報の取得関数
def scrape_worker_profiles(base_url_list):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    profile_set = set()

    # 除外する年齢条件
    excluded_ages = [
        "40代後半", "50代前半", "50代後半",
        "60代前半", "60代後半", "70代前半", "70代後半",
        "80代前半", "80代後半", "90代前半", "90代後半"
    ]

    # 除外する最終アクセス条件（正規表現で対応）
    excluded_access_periods = [
        r"[1-9]ヶ月前",             # 1ヶ月前〜9ヶ月前
        r"1[0-2]ヶ月前",           # 10ヶ月前〜12ヶ月前
        r"1年.*前",                # 1年前、1年弱前、1年強前
        r"2年.*前",                # 2年前、2年弱前、2年強前
        r"3年.*前",                # 3年前、3年弱前、3年強前
        r"4年.*前",                # 4年前、4年弱前、4年強前
        r"5年.*前",                # 5年前、5年弱前、5年強前
        r"6年.*前",                # 6年前、6年弱前、6年強前
        r"7年.*前",                # 7年前、7年弱前、7年強前
        r"8年.*前",                # 8年前、8年弱前、8年強前
        r"9年.*前",                # 9年前、9年弱前、9年強前
        r"1[0-2]年.*前"           # 10年前〜12年前
    ]

    for base_url in base_url_list:
        page = 1
        while True:
            st.info(f"ページ {page} を取得中...")  # ページの進行状況を表示
            url = f"{base_url}&page={page}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                st.warning(f"ページ {page} の取得に失敗しました: {url}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            feedback_container = soup.find('div', id='feedbacks-container')
            if not feedback_container:
                st.warning(f"ページ {page} に評価データが見つかりませんでした: {url}")
                break

            data = feedback_container.get('data')
            if not data:
                st.warning(f"ページ {page} に評価データが見つかりませんでした: {url}")
                break

            feedback_data = json.loads(data)
            user_ratings = feedback_data.get('feedbacks', {}).get('user_ratings', [])
            if not user_ratings:
                st.info(f"ページ {page} に評価が見つかりませんでした: {url}")
                break

            for rating in user_ratings:
                job_title = rating.get('job_offer_title', '')
                user_id = rating.get('user_id')
                if "記事・Webコンテンツ作成の仕事" in job_title and user_id:
                    profile_url = f"https://crowdworks.jp/public/employees/{user_id}"
                    profile_response = requests.get(profile_url, headers=headers)
                    if profile_response.status_code != 200:
                        continue
                    profile_soup = BeautifulSoup(profile_response.text, 'html.parser')

                    not_found_message = profile_soup.find('div', class_='message-404')
                    if not_found_message:
                        continue

                    # 年齢条件の除外
                    attributes = profile_soup.find('p', class_='attributes')
                    if attributes:
                        age_text = attributes.text.strip()
                        if any(age in age_text for age in excluded_ages):
                            continue

                    # 最終アクセス条件の除外
                    last_activity = profile_soup.find('p', class_='last_activity')
                    if last_activity:
                        access_date = last_activity.text.replace('最終アクセス: ', '').strip()
                        # 正規表現で一致する場合に除外
                        if any(re.search(period, access_date) for period in excluded_access_periods):
                            continue

                    profile_set.add(profile_url)

            page += 1  # 次のページへ
            time.sleep(0.5)  # サーバー負荷を軽減

    return list(profile_set)

# セッションステートでURLリストを管理
if "url_list" not in st.session_state:
    st.session_state.url_list = [""]

def add_url(index):
    st.session_state.url_list.insert(index + 1, "")

def remove_url(index):
    if len(st.session_state.url_list) > 1:
        st.session_state.url_list.pop(index)

# タイトル
st.title("ワーカー洗い出し")

# 各URL入力欄と追加/削除ボタン
for i, url in enumerate(st.session_state.url_list):
    cols = st.columns([5, 1, 1])
    with cols[0]:
        st.session_state.url_list[i] = st.text_input(f"事業者URL {i+1}", value=url, key=f"url_{i}")
    with cols[1]:
        # プラスボタン
        if st.button("＋", key=f"add_{i}"):
            add_url(i)
    with cols[2]:
        # マイナスボタン
        if st.button("－", key=f"remove_{i}"):
            remove_url(i)

# 開始ボタン
if st.button("開始"):
    # プログレスバーの追加
    with st.spinner("データを取得中..."):
        results = scrape_worker_profiles(st.session_state.url_list)
        if results:
            st.success(f"条件に合致したプロフィールURL数: {len(results)}")
            # 結果を表示（編集不可）
            result_text = "\n".join(results)
            st.code(result_text, language="text")  # 編集不可の結果表示

            # ダウンロードボタン
            st.download_button("ダウンロード", data=result_text, file_name="profiles.txt", mime="text/plain")
        else:
            st.error("条件に合致するプロフィールURLが見つかりませんでした。")
