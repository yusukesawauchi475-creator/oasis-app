import { initializeApp } from "firebase/app";
import { getFirestore, collection, getDocs, doc, getDoc } from "firebase/firestore";

const app = initializeApp({
  apiKey: "AIzaSyDXQabNFmpISVQ4O_yCP6dTyx-UC_uGQLw",
  authDomain: "oasis-bde20.firebaseapp.com",
  projectId: "oasis-bde20",
});

const db = getFirestore(app);

// Manhattan bbox (SSOT: center 40.754, -74.003)
const BBOX = { latMin: 40.680, latMax: 40.880, lngMin: -74.050, lngMax: -73.900 };

function englishRatio(name) {
  if (!name) return 0;
  const alpha = [...name].filter(c => /\p{L}/u.test(c));
  if (alpha.length === 0) return 0;
  const ascii = alpha.filter(c => /[a-zA-Z]/.test(c));
  return ascii.length / alpha.length;
}

function isOutsideBbox(t) {
  const { lat, lng } = t;
  if (lat == null || lng == null) return true;
  return lat < BBOX.latMin || lat > BBOX.latMax || lng < BBOX.lngMin || lng > BBOX.lngMax;
}

function hasEnglishHours(hours) {
  if (!hours || typeof hours !== "string") return false;
  return /\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Open|Closed|Hours|AM|PM|am|pm|24\s*hours|24\/7)\b/.test(hours)
    || /\d{1,2}:\d{2}\s*(AM|PM|am|pm)/.test(hours);
}

async function main() {
  console.log("Fetching Manhattan data from Firestore (oasis-bde20)...\n");

  let allToilets = [];

  // Method: get all docs in 'toilets' collection, filter manhattan chunks
  const snap = await getDocs(collection(db, "toilets"));
  console.log(`Total docs in 'toilets' collection: ${snap.docs.length}`);

  const manhattanDocs = [];
  snap.docs.forEach(d => {
    if (d.id.startsWith("manhattan_chunk_") || d.id === "manhattan") {
      manhattanDocs.push(d);
    }
  });

  console.log(`Manhattan docs found: ${manhattanDocs.length}`);
  // Also show all doc IDs for reference
  const allIds = snap.docs.map(d => d.id).filter(id => id.includes("manhattan"));
  console.log(`Doc IDs containing 'manhattan': ${allIds.join(", ")}`);

  for (const d of manhattanDocs) {
    const data = d.data();
    const items = data.items || data.data || [];
    console.log(`  ${d.id}: ${items.length} items`);
    allToilets = allToilets.concat(items);
  }

  if (!allToilets.length) {
    console.log("\nNo toilet data found for Manhattan.");
    console.log("All doc IDs:", snap.docs.map(d => d.id).join(", "));
    process.exit(1);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log(`TOTAL MANHATTAN TOILETS: ${allToilets.length}`);
  console.log(`${"=".repeat(60)}\n`);

  // [1] English name ratio >= 50%
  const engNames = allToilets.filter(t => englishRatio(t.name) >= 0.5);
  console.log(`[1] name英字50%以上: ${engNames.length} 件 / ${allToilets.length} 件 (${(engNames.length / allToilets.length * 100).toFixed(1)}%)`);
  engNames.slice(0, 8).forEach(t => {
    console.log(`    ${t.name} (ratio=${(englishRatio(t.name) * 100).toFixed(0)}%, cat=${t.cat})`);
  });

  // [2] Outside bbox
  const outside = allToilets.filter(isOutsideBbox);
  console.log(`\n[2] bbox外: ${outside.length} 件`);
  console.log(`    bbox: lat ${BBOX.latMin}-${BBOX.latMax}, lng ${BBOX.lngMin}-${BBOX.lngMax}`);
  outside.slice(0, 15).forEach(t => {
    console.log(`    ${t.name || "?"}: (${t.lat}, ${t.lng})`);
  });

  // [3] tier=4 AND cat=Public
  const t4pub = allToilets.filter(t => t.tier === 4 && t.cat === "Public");
  console.log(`\n[3] tier=4 & cat=Public: ${t4pub.length} 件`);
  t4pub.slice(0, 15).forEach(t => {
    console.log(`    ${t.name || "?"} (id=${t.id || "?"})`);
  });

  // [4] English hours
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

  // Tier distribution
  const tierDist = {};
  allToilets.forEach(t => { tierDist[t.tier] = (tierDist[t.tier] || 0) + 1; });
  console.log(`\n  Tier分布: ${JSON.stringify(tierDist)}`);

  // Cat distribution
  const catDist = {};
  allToilets.forEach(t => { catDist[t.cat] = (catDist[t.cat] || 0) + 1; });
  console.log(`  Cat分布:  ${JSON.stringify(catDist)}`);

  // Source distribution
  const srcDist = {};
  allToilets.forEach(t => { srcDist[t.source || "none"] = (srcDist[t.source || "none"] || 0) + 1; });
  console.log(`  Source分布: ${JSON.stringify(srcDist)}`);

  process.exit(0);
}

main().catch(e => { console.error(e); process.exit(1); });
