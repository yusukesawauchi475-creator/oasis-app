import { initializeApp } from "firebase/app";
import { getFirestore, doc, getDoc } from "firebase/firestore";
import { getAuth, signInAnonymously } from "firebase/auth";

const app = initializeApp({
  apiKey: "AIzaSyDXQabNFmpISVQ4O_yCP6dTyx-UC_uGQLw",
  authDomain: "oasis-bde20.firebaseapp.com",
  projectId: "oasis-bde20",
});

const auth = getAuth(app);
const db = getFirestore(app);

const BBOX = { latMin: 40.680, latMax: 40.880, lngMin: -74.050, lngMax: -73.900 };

function englishRatio(name) {
  if (!name) return 0;
  const alpha = [...name].filter(c => /\p{L}/u.test(c));
  if (alpha.length === 0) return 0;
  const ascii = alpha.filter(c => /[a-zA-Z]/.test(c));
  return ascii.length / alpha.length;
}

function isOutsideBbox(t) {
  if (t.lat == null || t.lng == null) return true;
  return t.lat < BBOX.latMin || t.lat > BBOX.latMax || t.lng < BBOX.lngMin || t.lng > BBOX.lngMax;
}

function hasEnglishHours(hours) {
  if (!hours || typeof hours !== "string") return false;
  return /\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Open|Closed|Hours|AM|PM|am|pm|24\s*hours|24\/7)\b/.test(hours)
    || /\d{1,2}:\d{2}\s*(AM|PM|am|pm)/.test(hours);
}

async function main() {
  console.log("Signing in anonymously...");
  await signInAnonymously(auth);
  console.log("OK\n");

  let allToilets = [];

  // Try various doc ID patterns
  const patterns = [
    // chunk pattern
    ...Array.from({length: 20}, (_, i) => `manhattan_chunk_${i}`),
    // single doc
    "manhattan",
    // other patterns
    "Manhattan",
    "manhattan_0",
    "manhattan_1",
  ];

  console.log("Probing document IDs...");
  for (const id of patterns) {
    try {
      const snap = await getDoc(doc(db, "toilets", id));
      if (snap.exists()) {
        const data = snap.data();
        const items = data.items || data.data || data.toilets || [];
        const keys = Object.keys(data);
        console.log(`  ✓ ${id}: ${items.length} items, fields: [${keys.join(", ")}]`);
        if (items.length === 0 && keys.length > 0) {
          // Maybe it's structured differently
          console.log(`    Sample keys: ${keys.slice(0, 5).join(", ")}`);
          const firstVal = data[keys[0]];
          console.log(`    First value type: ${typeof firstVal}, isArray: ${Array.isArray(firstVal)}`);
          if (typeof firstVal === 'object' && firstVal !== null) {
            console.log(`    First value keys: ${Object.keys(firstVal).slice(0, 5).join(", ")}`);
          }
        }
        allToilets = allToilets.concat(items);
      } else {
        if (id === "manhattan" || id === "manhattan_chunk_0") {
          console.log(`  ✗ ${id}: not found`);
        }
      }
    } catch (e) {
      console.log(`  ✗ ${id}: ${e.code || e.message}`);
      if (id === "manhattan_chunk_0") break; // If permission denied, stop
    }
  }

  if (!allToilets.length) {
    console.log("\nNo data via known patterns. Trying to discover doc structure...");
    // Try getting manhattan doc and inspect deeply
    try {
      const snap = await getDoc(doc(db, "toilets", "manhattan"));
      if (snap.exists()) {
        const data = snap.data();
        console.log(`manhattan doc fields: ${JSON.stringify(Object.keys(data))}`);
        console.log(`Data sample: ${JSON.stringify(data).substring(0, 500)}`);
      }
    } catch (e) {
      console.log(`Error: ${e.message}`);
    }
    process.exit(1);
  }

  // Sample first toilet
  console.log(`\nSample: ${JSON.stringify(allToilets[0], null, 2)}`);

  console.log(`\n${"=".repeat(60)}`);
  console.log(`TOTAL MANHATTAN TOILETS: ${allToilets.length}`);
  console.log(`${"=".repeat(60)}\n`);

  // [1]
  const engNames = allToilets.filter(t => englishRatio(t.name) >= 0.5);
  console.log(`[1] name英字50%以上: ${engNames.length} 件 / ${allToilets.length} 件 (${(engNames.length / allToilets.length * 100).toFixed(1)}%)`);
  engNames.slice(0, 8).forEach(t => {
    console.log(`    ${t.name} (${(englishRatio(t.name) * 100).toFixed(0)}%, cat=${t.cat}, tier=${t.tier})`);
  });

  // [2]
  const outside = allToilets.filter(isOutsideBbox);
  console.log(`\n[2] bbox外: ${outside.length} 件  (bbox: lat ${BBOX.latMin}–${BBOX.latMax}, lng ${BBOX.lngMin}–${BBOX.lngMax})`);
  outside.slice(0, 15).forEach(t => {
    console.log(`    ${t.name || "?"}: (${t.lat}, ${t.lng})`);
  });

  // [3]
  const t4pub = allToilets.filter(t => t.tier === 4 && t.cat === "Public");
  console.log(`\n[3] tier=4 & cat=Public: ${t4pub.length} 件`);
  t4pub.slice(0, 15).forEach(t => {
    console.log(`    ${t.name || "?"} (id=${t.id || "?"})`);
  });

  // [4]
  const withHours = allToilets.filter(t => t.hours);
  const engHours = allToilets.filter(t => hasEnglishHours(t.hours));
  console.log(`\n[4] hours英語表記: ${engHours.length} 件 / hours有り ${withHours.length} 件`);
  engHours.slice(0, 10).forEach(t => {
    console.log(`    ${t.name || "?"}: "${t.hours}"`);
  });

  // Summary
  console.log(`\n${"=".repeat(60)}`);
  console.log("AUDIT SUMMARY");
  console.log(`${"=".repeat(60)}`);
  console.log(`  総件数:              ${allToilets.length}`);
  console.log(`  [1] 英字名50%+:     ${engNames.length} (${(engNames.length / allToilets.length * 100).toFixed(1)}%)`);
  console.log(`  [2] bbox外:         ${outside.length}`);
  console.log(`  [3] T4+Public:      ${t4pub.length}`);
  console.log(`  [4] 英語hours:      ${engHours.length}`);

  const tierDist = {};
  allToilets.forEach(t => { tierDist[t.tier ?? "none"] = (tierDist[t.tier ?? "none"] || 0) + 1; });
  console.log(`\n  Tier分布: ${JSON.stringify(tierDist)}`);

  const catDist = {};
  allToilets.forEach(t => { catDist[t.cat ?? "none"] = (catDist[t.cat ?? "none"] || 0) + 1; });
  console.log(`  Cat分布:  ${JSON.stringify(catDist)}`);

  const srcDist = {};
  allToilets.forEach(t => { srcDist[t.source || "none"] = (srcDist[t.source || "none"] || 0) + 1; });
  console.log(`  Source分布: ${JSON.stringify(srcDist)}`);

  process.exit(0);
}

main().catch(e => { console.error(e); process.exit(1); });
