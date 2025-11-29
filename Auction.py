import streamlit as st
import pandas as pd
import io
import re
import json
import os

st.set_page_config(layout="wide")
st.title("🏏 COMPLETE Cricket Auction App")

# PERSISTENT STORAGE
DATA_FILE = "auction_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'players': [],
        'teams': {f'Team {i+1}': {'budget': 5000, 'players': []} for i in range(6)},
        'team_names': [f'Team {i+1}' for i in range(8)],
        'current': 0,
        'auction_history': []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Load ALL data
data = load_data()
for key, value in data.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 1. IMPORT GOOGLE FORM DATA
st.header("📥 1. Import Google Form Players")
csv_data = st.text_area("Paste your tab-separated data:", height=150, 
                       placeholder="11/29/2025 12:08:42	Soumya Ranjan Das	18	ALLRONDER	https://drive...")

if st.button("✅ IMPORT PLAYERS", type="primary"):
    lines = csv_data.strip().split('\n')
    players = []
    for line in lines:
        if line.strip() and not line.startswith('Timestamp'):
            parts = re.split(r'\t+', line.strip())
            if len(parts) >= 4:
                players.append({
                    'name': parts[1].strip(),
                    'age': parts[2].strip(),
                    'type': parts[3].strip().replace('ALLRONDER', 'All-rounder').replace('BATSMAN', 'Batsman'),
                    'photo_url': parts[4].strip() if len(parts) > 4 else "",
                    'price': 0,
                    'sold_to': None
                })
    st.session_state.players = players
    data['players'] = players
    save_data(data)
    st.success(f"✅ {len(players)} players imported & saved!")
    st.rerun()

# 2. TEAM SETUP
st.header("🏆 2. Customize 8 Teams")
cols = st.columns(4)
for i in range(8):
    with cols[i%4]:
        new_name = st.text_input(f"T{i+1}", value=st.session_state.team_names[i], key=f"t{i}")
        if st.button("💾", key=f"s{i}"):
            old = st.session_state.team_names[i]
            st.session_state.teams[new_name] = st.session_state.teams.pop(old)
            st.session_state.team_names[i] = new_name
            data['team_names'] = st.session_state.team_names
            save_data(data)
            st.rerun()

# 3. LIVE AUCTION (MAIN FEATURE)
if st.session_state.players:
    st.header("⚡ 3. LIVE AUCTION")
    tab1, tab2, tab3 = st.tabs(["🎯 CURRENT PLAYER", "📊 AUCTION HISTORY", "📋 ALL PLAYERS"])
    
    with tab1:
        st.markdown(f"### **Player {st.session_state.current + 1}/{len(st.session_state.players)}**")
        
        # SIDEBAR: LIVE BUDGETS
        st.sidebar.title("💰 LIVE BUDGETS")
        for tname in st.session_state.team_names:
            team = st.session_state.teams[tname]
            spent = sum(p['price'] for p in team['players'])
            st.sidebar.metric(tname[:12], f"₹{team['budget'] - spent:,}", f"-₹{spent:,}")
        
        # CURRENT PLAYER DISPLAY
        player = st.session_state.players[st.session_state.current]
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### 👨 **{player['name']}**")
            st.markdown(f"**{player['type']}** | Age: **{player['age']}**")
            if player['photo_url']:
                st.markdown(f"[📸 View Photo]({player['photo_url']})")
        
        with col2:
            bid = st.number_input("💰 BID AMOUNT", 0, 5000, 500, 100, key="bid")
        
        with col3:
            team = st.selectbox("🏆 TEAM", st.session_state.team_names, key="team")
        
        # AUCTION BUTTONS
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("✅ **SOLD!**", type="primary", use_container_width=True):
                player['price'] = bid
                player['sold_to'] = team
                
                # ADD TO HISTORY
                st.session_state.auction_history.append({
                    'time': pd.Timestamp.now().strftime('%H:%M:%S'),
                    'player': player['name'],
                    'type': player['type'],
                    'age': player['age'],
                    'bid': bid,
                    'team': team
                })
                
                # ADD TO TEAM
                st.session_state.teams[team]['players'].append(player.copy())
                
                # NEXT PLAYER
                st.session_state.current += 1
                if st.session_state.current >= len(st.session_state.players):
                    st.session_state.current = 0
                
                # SAVE EVERYTHING
                data.update({
                    'players': st.session_state.players,
                    'teams': st.session_state.teams,
                    'team_names': st.session_state.team_names,
                    'current': st.session_state.current,
                    'auction_history': st.session_state.auction_history
                })
                save_data(data)
                st.rerun()
        
        with col_b2:
            if st.button("⏭️ **NEXT**", use_container_width=True):
                st.session_state.current += 1
                if st.session_state.current >= len(st.session_state.players):
                    st.session_state.current = 0
                data['current'] = st.session_state.current
                save_data(data)
                st.rerun()
        
        with col_b3:
            if st.button("🔄 **RESET**", use_container_width=True):
                st.session_state.current = 0
                data['current'] = 0
                save_data(data)
                st.rerun()
        
        st.progress(st.session_state.current / len(st.session_state.players))
    
    with tab2:
        st.header("📊 AUCTION HISTORY")
        if st.session_state.auction_history:
            df = pd.DataFrame(st.session_state.auction_history)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("👆 Start bidding!")
    
    with tab3:
        st.header("📋 ALL PLAYERS")
        df = pd.DataFrame(st.session_state.players)
        st.dataframe(df, use_container_width=True)

# 4. DOWNLOAD RESULTS
st.header("📥 4. Download Results")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 SUMMARY", type="primary"):
        summary = pd.DataFrame([{
            'Team': t,
            'Budget Left': data['teams'][t]['budget'] - sum(p['price'] for p in data['teams'][t]['players']),
            'Players': len(data['teams'][t]['players'])
        } for t in st.session_state.team_names])
        csv = summary.to_csv(index=False)
        st.download_button("⬇️ Download", csv, "auction_summary.csv", "text/csv")

with col2:
    if st.button("📋 HISTORY", type="secondary"):
        if st.session_state.auction_history:
            csv = pd.DataFrame(st.session_state.auction_history).to_csv(index=False)
            st.download_button("⬇️ Download", csv, "auction_history.csv", "text/csv")

with col3:
    if st.button("🗑️ CLEAR ALL DATA", type="secondary"):
        os.remove(DATA_FILE)
        st.experimental_rerun()

st.markdown("---")
st.caption("✅ **COMPLETE AUCTION SYSTEM** - Import → Teams → Bid → History → Download")
