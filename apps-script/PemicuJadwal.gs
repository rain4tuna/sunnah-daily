/**
 * Pemicu jadwal tayang Sunnah Daily (pengganti jadwal GitHub yang sering telat 30-45 menit).
 * Cara pasang:
 *  1. script.google.com -> New project -> tempel file ini.
 *  2. Project Settings -> Script properties -> Add: GITHUB_TOKEN = token fine-grained (repo sunnah-daily, Actions: Read and write).
 *  3. Jalankan fungsi pasangPemicu() sekali (izinkan akses).
 * Script mengecek tiap 5 menit dan menekan "Run workflow" di GitHub tepat di jam tayang.
 * Jadwal GitHub tetap jadi cadangan; kalau telat, slotnya otomatis dilewati karena sudah ada postingan.
 */
var REPO = 'rain4tuna/sunnah-daily';
var WORKFLOW = 'buat-video.yml';
var SLOT = ['05:17', '11:47', '15:37', '18:47', '21:13'];   // WIB

function cekJadwal() {
  var sekarang = new Date();
  var jam = Utilities.formatDate(sekarang, 'Asia/Jakarta', 'HH:mm');
  var tanggal = Utilities.formatDate(sekarang, 'Asia/Jakarta', 'yyyy-MM-dd');
  var menitKini = toMenit(jam);
  var prop = PropertiesService.getScriptProperties();
  SLOT.forEach(function (s) {
    var selisih = menitKini - toMenit(s);
    var kunci = 'sudah_' + tanggal + '_' + s;
    if (selisih >= 0 && selisih < 10 && !prop.getProperty(kunci)) {
      jalankan();
      prop.setProperty(kunci, jam);
      Logger.log('Memicu slot ' + s + ' pada ' + jam);
    }
  });
}

function jalankan() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  var res = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/dispatches', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json' },
    payload: JSON.stringify({ ref: 'main', inputs: { uji: 'false', posting_ig: 'true', posting_yt: 'true', tema: 'auto' } }),
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 204) throw new Error('GitHub menolak: ' + res.getResponseCode() + ' ' + res.getContentText());
}

function toMenit(hhmm) {
  var p = hhmm.split(':');
  return parseInt(p[0], 10) * 60 + parseInt(p[1], 10);
}

function pasangPemicu() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('cekJadwal').timeBased().everyMinutes(5).create();
  Logger.log('Pemicu tiap 5 menit terpasang.');
}

/** Uji: jalankan sekali untuk memastikan token benar (akan memposting 1 video!). */
function ujiSekali() { jalankan(); }
