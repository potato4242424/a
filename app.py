import streamlit as st
import pandas as pd
import time
import os
import hashlib
from datetime import date

st.set_page_config(page_title="筋肉ラボFitly", layout="centered")

USER_FILE = "users.csv"
LOG_FILE = "training_log.csv"

if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["user", "password"]).to_csv(USER_FILE, index=False)

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["user", "date", "exercise", "count"]).to_csv(LOG_FILE, index=False)

# ===============================
# 関数
# ===============================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def bmi_type(bmi):
    if bmi < 18.5:
        return "やせ型"
    elif bmi < 25:
        return "標準体重"
    else:
        return "肥満体型"

def amino_level(a):
    if a >= 18: return 4
    elif a >= 15: return 3
    elif a >= 13: return 2
    elif a >= 10: return 1
    else: return 0

def adjust_count(base, diff):
    rate = {"簡単":0.8, "普通":1.0, "難しい":1.2}
    return int(base * rate[diff])

# ===============================
# メニュー構成（背中含む）
# ===============================
menus = {
    "腕":["プッシュアップ","ワイドプッシュアップ","ダイヤモンドプッシュアップ","インクラインプッシュアップ","パイクプッシュアップ"],
    "脚":["スクワット","ブルガリアンスクワット","ランジ","ジャンプスクワット","カーフレイズ"],
    "腹":["クランチ","レッグレイズ","ロシアンツイスト","プランク","バイシクルクランチ"],
    "背中":["バックエクステンション","リバーススノーエンジェル","スーパーマン","ヒップリフト","タオルローイング"]
}

base_counts = {
    "腕":[10,12,15,18,20],
    "脚":[15,18,20,25,30],
    "腹":[15,20,25,30,35],
    "背中":[12,15,18,20,25]
}

# ===============================
# セッション
# ===============================
for k in ["login_user","bmi","bmi_result","amino","age"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ===============================
# ログイン
# ===============================
if st.session_state.login_user is None:
    st.title("筋肉ラボFitly")
    u = st.text_input("ユーザー名")
    p = st.text_input("パスワード", type="password")
    users = pd.read_csv(USER_FILE)

    if st.button("ログイン"):
        if ((users.user==u)&(users.password==hash_password(p))).any():
            st.session_state.login_user = u
            st.rerun()
        else:
            st.error("ログイン失敗")

    if st.button("新規登録"):
        pd.concat([users,pd.DataFrame([[u,hash_password(p)]],columns=["user","password"])]).to_csv(USER_FILE,index=False)
        st.success("登録完了")
    st.stop()

# ===============================
# ページ選択
# ===============================
page = st.radio("メニュー",["BMI","メニュー作成","記録","タイマー","記録グラフ"],horizontal=True)

# ===============================
# BMI
# ===============================
if page=="BMI":
    h = st.number_input("身長(cm)",150,200,170)
    w = st.number_input("体重(kg)",40,150,60)
    age = st.number_input("年齢",10,90,20)

    if st.button("判定"):
        bmi = round(w/((h/100)**2),2)
        amino = 5 + (10 if age<=30 else 8)

        st.session_state.bmi = bmi
        st.session_state.bmi_result = bmi_type(bmi)
        st.session_state.amino = amino
        st.session_state.age = age

        st.success(f"BMI：{bmi}（{st.session_state.bmi_result}）")

# ===============================
# メニュー作成（提案専用）
# ===============================
# ===============================
# メニュー作成（提案専用）
# ===============================
if page=="メニュー作成":
    if st.session_state.bmi is None:
        st.warning("先にBMI判定をしてください")
        st.stop()

    part = st.selectbox("部位", list(menus.keys()))

    difficulty = st.radio(
        "難易度を選択してください",
        ["簡単","普通","難しい"],
        index=None,  # ← これが重要（未選択状態）
        horizontal=True
    )

    if difficulty is None:
        st.info("難易度を選ぶと推奨回数が表示されます")
        st.stop()

    lv = amino_level(st.session_state.amino)

    for ex in menus[part]:
        base = base_counts[part][lv]

        if st.session_state.age >= 60:
            base = int(base * 0.7)

        if st.session_state.bmi_result == "肥満体型":
            base = int(base * 0.85)

        count = adjust_count(base, difficulty)

        st.subheader(ex)
        st.write(f"推奨回数：{count}")

        # 動画リンク（ワンクリック）
        st.link_button(
            "動画を見る",
            f"https://www.youtube.com/results?search_query={ex}",
            use_container_width=True
        )

# ===============================
# 記録ページ（完全独立）
# ===============================
if page=="記録":
    part = st.selectbox("部位", list(menus.keys()))
    exercise = st.selectbox("種目", menus[part])
    count = st.number_input("実施回数",1,300,10)

    if st.button("記録する"):
        log = pd.read_csv(LOG_FILE)
        log.loc[len(log)] = [
            st.session_state.login_user,
            date.today(),
            exercise,
            count
        ]
        log.to_csv(LOG_FILE,index=False)
        st.success("記録しました")

# ===============================
# インターバルタイマー
# ===============================
if page=="タイマー":
    work = st.slider("運動秒数",10,180,40)
    rest = st.slider("休憩秒数",5,180,20)
    rounds = st.slider("セット数",1,10,3)

    if st.button("スタート"):
        total = rounds * (work + rest)
        progress = st.progress(0)
        counter = 0

        for r in range(rounds):
            st.subheader(f"{r+1}セット目：運動")
            for i in range(work):
                counter += 1
                progress.progress(counter/total)
                time.sleep(1)

            st.subheader(f"{r+1}セット目：休憩")
            for i in range(rest):
                counter += 1
                progress.progress(counter/total)
                time.sleep(1)

        st.success("終了")

# ===============================
# グラフ
# ===============================
if page=="記録グラフ":
    df = pd.read_csv(LOG_FILE)
    df = df[df.user==st.session_state.login_user]
    if df.empty:
        st.info("記録なし")
    else:
        g = df.groupby("date")["count"].sum()
        st.line_chart(g)