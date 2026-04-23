// Monthly refresh — check for new places in existing cities
// Runs via GitHub Actions on 1st of each month
const admin = require('firebase-admin');
const fetch = require('node-fetch');

if (!admin.apps.length) {
  admin.initializeApp({ credential: admin.credential.cert(JSON.parse(process.env.FIREBASE_SA_KEY)) });
}
const db = admin.firestore();
const API_KEY = process.env.PLACES_API_KEY;
if (!API_KEY) {
  console.error('ERROR: PLACES_API_KEY environment variable is required');
  process.exit(1);
}

const JP_CITIES = ['tokyo','osaka','kobe','fukuoka','sapporo','nagoya','kyoto','hiroshima','naha','kagoshima'];
const CITIES = {
  manhattan: { bbox: { minLat:40.700, maxLat:40.780, minLng:-74.020, maxLng:-73.940 } },
  tokyo:     { bbox: { minLat:35.650, maxLat:35.720, minLng:139.700, maxLng:139.790 } },
  osaka:     { bbox: { minLat:34.650, maxLat:34.710, minLng:135.470, maxLng:135.540 } },
  kobe:      { bbox: { minLat:34.660, maxLat:34.710, minLng:135.160, maxLng:135.220 } },
  london:    { bbox: { minLat:51.490, maxLat:51.530, minLng:-0.140, maxLng:-0.050 } },
};
// Sample center areas only (not full bbox) to stay in free quota

const TYPES = ['public_bathroom','convenience_store'];
const GRID = 0.01; // ~1.1km, coarse grid for sampling

async function searchNearby(lat, lng, type, isJP) {
  try {
    const res = await fetch('https://places.googleapis.com/v1/places:searchNearby', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.types',
      },
      body: JSON.stringify({
        includedTypes: [type], maxResultCount: 20,
        locationRestriction: { circle: { center: { latitude: lat, longitude: lng }, radius: 1000 } },
        languageCode: isJP ? 'ja' : 'en',
      }),
    });
    return (await res.json()).places || [];
  } catch(e) { return []; }
}

(async () => {
  console.log('=== Monthly Refresh ===');
  console.log(`Date: ${new Date().toISOString()}`);
  let totalNew = 0, totalReqs = 0;

  for (const [city, cfg] of Object.entries(CITIES)) {
    const isJP = JP_CITIES.includes(city);
    const existingIds = new Set();
    for (let i = 0; i < 15; i++) {
      const s = await db.collection('cities').doc(city).collection('chunks').doc(`${i}`).get();
      if (s.exists) (s.data().toilets || []).forEach(t => existingIds.add(t.id));
    }

    const newPlaces = [];
    const seen = new Set();
    const b = cfg.bbox;
    for (const type of TYPES) {
      for (let lat = b.minLat; lat <= b.maxLat; lat += GRID) {
        for (let lng = b.minLng; lng <= b.maxLng; lng += GRID) {
          totalReqs++;
          const places = await searchNearby(lat, lng, type, isJP);
          for (const p of places) {
            if (seen.has(p.id) || existingIds.has(p.id)) continue;
            seen.add(p.id);
            newPlaces.push({
              id: p.id,
              name: (p.displayName && p.displayName.text) || '',
              lat: p.location.latitude, lng: p.location.longitude,
              tier: type === 'public_bathroom' ? 1 : 2,
              cat: type === 'public_bathroom' ? 'Public' : 'Store',
              free: type === 'public_bathroom', isPartner: false, isUnconfirmed: false,
              hours: null, source: 'google', types: (p.types || []).slice(0, 5),
            });
          }
          await new Promise(r => setTimeout(r, 100));
        }
      }
    }

    if (newPlaces.length > 0) {
      // Find chunk with space
      for (let i = 0; i < 15; i++) {
        const ref = db.collection('cities').doc(city).collection('chunks').doc(`${i}`);
        const snap = await ref.get();
        const arr = snap.exists ? (snap.data().toilets || []) : [];
        if (arr.length < 500) {
          const batch = newPlaces.splice(0, 500 - arr.length);
          await ref.set({ toilets: [...arr, ...batch] });
          if (newPlaces.length === 0) break;
        }
      }
    }

    totalNew += seen.size - existingIds.size > 0 ? newPlaces.length : 0;
    console.log(`${city}: existing=${existingIds.size} new=${seen.size > 0 ? newPlaces.length : 0} requests=${totalReqs}`);
  }

  console.log(`\nTotal new places: ${totalNew}`);
  console.log(`Total API requests: ${totalReqs}`);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
