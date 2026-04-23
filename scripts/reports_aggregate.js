// Symlink/copy of ~/oasis-ingest/reports_aggregate.js for GitHub Actions
// See ~/oasis-ingest/reports_aggregate.js for full implementation
const admin = require('firebase-admin');
if (!admin.apps.length) {
  admin.initializeApp({ credential: admin.credential.cert(JSON.parse(process.env.FIREBASE_SA_KEY)) });
}
const db = admin.firestore();

const THRESHOLD = 3;
const CLOSED_REASONS = ['rptClosed', 'rptNoToilet'];
const CITIES = ['manhattan','tokyo','osaka','kobe','london','sydney','melbourne','brisbane',
  'fukuoka','sapporo','nagoya','kyoto','hiroshima','naha','kagoshima'];

(async () => {
  console.log('=== Reports Aggregation ===');
  const reportsSnap = await db.collection('reports').get();
  console.log(`Total reports: ${reportsSnap.size}`);
  const counts = {};
  reportsSnap.forEach(doc => {
    const d = doc.data();
    if (d.toiletId && CLOSED_REASONS.includes(d.reason)) counts[d.toiletId] = (counts[d.toiletId] || 0) + 1;
  });
  const flagged = Object.entries(counts).filter(([, c]) => c >= THRESHOLD);
  console.log(`Flagged: ${flagged.length}`);
  let downgraded = 0;
  for (const [toiletId, reportCount] of flagged) {
    for (const city of CITIES) {
      let found = false;
      for (let i = 0; i < 15; i++) {
        const ref = db.collection('cities').doc(city).collection('chunks').doc(`${i}`);
        const snap = await ref.get();
        if (!snap.exists) continue;
        const toilets = snap.data().toilets || [];
        const idx = toilets.findIndex(t => t.id === toiletId);
        if (idx === -1) continue;
        if (toilets[idx].tier === 4) { found = true; break; }
        const oldTier = toilets[idx].tier;
        toilets[idx] = { ...toilets[idx], tier: 4 };
        await ref.update({ toilets });
        await db.collection('stats').doc('autoDowngraded').collection('history').add({
          toiletId, toiletName: toilets[idx].name || '', cityKey: city, chunkIndex: i,
          oldTier, reportCount, downgradedAt: admin.firestore.FieldValue.serverTimestamp(),
        });
        console.log(`  DOWNGRADE ${toiletId} in ${city}/chunk${i}: ${oldTier}→4`);
        downgraded++;
        found = true;
        break;
      }
      if (found) break;
    }
  }
  console.log(`Downgraded: ${downgraded}`);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
