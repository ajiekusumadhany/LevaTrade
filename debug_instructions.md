# 🐛 DEBUG INDICATOR PERFORMANCE ISSUE

## 📋 Langkah-langkah Debug:

### 1. Buka Dashboard dengan Console
1. Buka browser dan kunjungi: **http://localhost:5000**
2. Tekan **F12** untuk membuka Developer Tools
3. Klik tab **Console**
4. Refresh halaman dengan **Ctrl+Shift+R** (hard refresh)

### 2. Test Indicator Performance
1. Klik **"Indicator Performance"** di sidebar
2. Perhatikan pesan di console
3. Cari pesan berikut:
   - `🖱️ showIndicatorPerformance clicked`
   - `🔍 Starting loadIndicatorPerformance...`
   - `📊 Mode: dry-run Days: 30`
   - `🌐 Fetching data from API...`
   - `📡 URL: /api/indicator-performance?mode=dry-run&days=30`
   - `📊 Response status: 200`
   - `✅ Data loaded successfully, displaying...`

### 3. Kemungkinan Error dan Solusi:

#### ❌ Error: "indicatorPerformanceModal not found!"
**Solusi:** Refresh halaman dengan Ctrl+Shift+R

#### ❌ Error: "indicator-overview element not found!"
**Solusi:** Modal tidak terbuka dengan benar, coba refresh

#### ❌ Error: "HTTP 500" atau "Network Error"
**Solusi:** Dashboard bermasalah, restart dengan `python dashboard_app.py`

#### ❌ Error: "Failed to fetch"
**Solusi:** 
- Cek apakah dashboard berjalan di http://localhost:5000
- Disable ad blocker atau browser extensions
- Coba browser lain (Chrome, Firefox, Edge)

### 4. Test Page Alternative
Jika masih bermasalah, coba test page:
1. Kunjungi: **http://localhost:5000/test**
2. Klik "Test Indicator Performance"
3. Lihat hasilnya

### 5. Manual API Test
Test API langsung di browser:
1. Buka tab baru
2. Kunjungi: **http://localhost:5000/api/indicator-performance?mode=dry-run&days=30**
3. Harus menampilkan JSON data dengan `"success": true`

## 🔧 Quick Fixes:

### Fix 1: Hard Refresh
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Fix 2: Clear Cache
```
F12 → Application → Storage → Clear site data
```

### Fix 3: Incognito Mode
```
Ctrl+Shift+N (Chrome)
Ctrl+Shift+P (Firefox)
```

### Fix 4: Restart Dashboard
```bash
# Stop current dashboard (Ctrl+C)
python dashboard_app.py
```

## 📊 Expected Console Output:
```
🖱️ showIndicatorPerformance clicked
📊 Current mode: dry-run
✅ Modal shown
🔍 Starting loadIndicatorPerformance...
📊 Mode: dry-run Days: 30
🌐 Fetching data from API...
📡 URL: /api/indicator-performance?mode=dry-run&days=30
📊 Response status: 200
📋 Response data: {success: true, indicators: {...}, ...}
✅ Data loaded successfully, displaying...
```

## 🎯 Jika Semua Gagal:
1. Screenshot error di console
2. Coba browser berbeda
3. Restart komputer
4. Check antivirus/firewall settings