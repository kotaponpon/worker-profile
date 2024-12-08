def scrape_worker_profiles(base_url_list):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    excluded_ages = ["50代後半", "60代前半", "60代後半", "70代前半"]
    excluded_access_periods = [
        "10ヶ月前", "11ヶ月前", "12ヶ月前",
        "1年前", "2年前", "3年前",
        "4年前", "5年前", "6年前"
    ]
    profile_set = set()

    for base_url in base_url_list:
        page = 1
        while True:
            # ページ番号を追加してURLを生成
            url = f"{base_url}&page={page}"
            response = requests.get(url, headers=headers)

            # HTTPエラーの処理
            if response.status_code != 200:
                st.warning(f"ページ {page} の取得に失敗しました: {url}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            feedback_container = soup.find('div', id='feedbacks-container')
            
            # データが存在しない場合、終了
            if not feedback_container:
                st.warning(f"ページ {page} に評価データが見つかりませんでした: {url}")
                break

            data = feedback_container.get('data')
            if not data:
                st.warning(f"ページ {page} に評価データが見つかりませんでした: {url}")
                break

            # JSONデータの解析
            feedback_data = json.loads(data)
            user_ratings = feedback_data.get('feedbacks', {}).get('user_ratings', [])

            # 評価がない場合、終了
            if not user_ratings:
                st.info(f"ページ {page} に評価がありません: {url}")
                break

            # 評価データを処理
            for rating in user_ratings:
                job_title = rating.get('job_offer_title', '')
                user_id = rating.get('user_id')
                if "記事・Webコンテンツ作成の仕事" in job_title and user_id:
                    profile_url = f"https://crowdworks.jp/public/employees/{user_id}"
                    profile_response = requests.get(profile_url, headers=headers)

                    # 個別プロフィールページの解析
                    if profile_response.status_code != 200:
                        continue
                    profile_soup = BeautifulSoup(profile_response.text, 'html.parser')

                    # 年齢と最終アクセス条件の除外
                    attributes = profile_soup.find('p', class_='attributes')
                    if attributes and any(age in attributes.text for age in excluded_ages):
                        continue
                    last_activity = profile_soup.find('p', class_='last_activity')
                    if last_activity:
                        access_date = last_activity.text.replace('最終アクセス: ', '').strip()
                        if any(period in access_date for period in excluded_access_periods):
                            continue

                    profile_set.add(profile_url)

            # 次のページへ
            page += 1
            time.sleep(0.5)  # サーバー負荷を軽減

    return list(profile_set)