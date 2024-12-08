import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

def scrape_worker_profiles(base_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    page = 1
    profile_set = set()

    # 除外条件
    excluded_ages = ["50代後半", "60代前半", "60代後半", "70代前半"]
    excluded_access_periods = [
        "10ヶ月前", "11ヶ月前", "12ヶ月前",
        "1年前", "2年前", "3年前",
        "4年前", "5年前", "6年前"
    ]

    while True:
        url = f"{base_url}&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.write(f"ページ {page} の取得に失敗しました")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        feedback_container = soup.find('div', id='feedbacks-container')
        if not feedback_container:
            st.write(f"ページ {page} に評価データが見つかりませんでした")
            break

        data = feedback_container.get('data')
        if not data:
            st.write(f"ページ {page} に評価データが見つかりませんでした")
            break

        feedback_data = json.loads(data)
        user_ratings = feedback_data.get('feedbacks', {}).get('user_ratings', [])
        if not user_ratings:
            st.write(f"ページ {page} に評価が見つかりません")
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

                # "ページが見つかりませんでした"のメッセージを確認
                not_found_message = profile_soup.find('div', class_='message-404')
                if not_found_message:
                    continue

                attributes = profile_soup.find('p', class_='attributes')
                if attributes and any(age in attributes.text for age in excluded_ages):
                    continue
                last_activity = profile_soup.find('p', class_='last_activity')
                if last_activity:
                    access_date = last_activity.text.replace('最終アクセス: ', '').strip()
                    if any(period in access_date for period in excluded_access_periods):
                        continue

                profile_set.add(profile_url)

        st.write(f"ページ {page} のデータを取得しました")
        page += 1

    return list(profile_set)

# Streamlitアプリ
st.title("Worker Profile Scraper")
base_url = st.text_input("評価URLを入力してください:")
if st.button("開始"):
    if base_url:
        profiles = scrape_worker_profiles(base_url)
        if profiles:
            st.write(f"条件に合致したプロフィールURL数: {len(profiles)}")
            st.write("条件に合致したプロフィールURL一覧:")
            for profile in profiles:
                st.write(profile)
        else:
            st.write("条件に合致するプロフィールURLが見つかりませんでした。URLを確認してください。")
    else:
        st.write("URLを入力してください")
