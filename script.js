import { doubleMetaphone } from 'https://esm.sh/double-metaphone@2?bundle';

// -------------------- Database helpers --------------------
let database = {};
let characters = [];
let currentChar = null;
let changedKeys = [];

async function loadDatabase() {
  const res = await fetch('/api/database');
  database = await res.json();
  characters = Object.keys(database); // <-- Move this here
}

async function updateDatabaseEntry(key, entry) {
  await fetch(`/api/database/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry)
  });
}

function markChanged(key) {
  if (!changedKeys.includes(key)) changedKeys.push(key);
}

async function saveChanges() {
  for (const key of changedKeys) {
    await updateDatabaseEntry(key, database[key]);
  }
}

async function saveAll() {
  for (const key of characters) {
    await updateDatabaseEntry(key, database[key]);
  }
}

async function updateQuizStatus() {
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  await fetch('/api/quiz-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lastCompleted: today }),
  });
}

function initDatabase() { //false negative answers and markings are only kept until the next run
  for (const key of Object.keys(database)) {
    const card = database[key];
    if (card.isFalseNegative){ 
      card.isFalseNegative = false;
      card.falseNegativeAnswer = [];
    }
    if (card.skipped) card.skipped = false; 
    if (card.isMarked) card.isMarked = false;
  }
}


// -------------------- Sheduling --------------------

function initSheduling() {
  for (const key of Object.keys(database)) {
    const card = database[key];
    if (!('interval' in card)) card.interval = 0;
    if (!('repetition' in card)) card.repetition = 0;
    if (!('ease' in card)) card.ease = 2.5;
    if (!('nextReview' in card)) card.nextReview = new Date().toISOString();
    if (!('isDue' in card)) card.isDue = true;
  }
}

async function updateDueCards() {
  const today = new Date();
  for (const key of Object.keys(database)) {
    const card = database[key];
    const nextReview = new Date(card.nextReview);
    if (key == "ancient"){
      console.log(nextReview <= today)
    }
    card.isDue = nextReview <= today;
  }
}

async function processAnswer(currentChar, passed) {
  const card = database[currentChar];
  
  if (!passed) {
    card.repetition = 0;
    card.interval = 1;
    card.ease = Math.max(1.3, card.ease - 0.2);
  } else {
    if (card.repetition === 0) {
      card.interval = 1;
    } else if (card.repetition === 1) {
      card.interval = 6;
    } else {
      card.interval = Math.round(card.interval * card.ease);
    }
    card.repetition += 1;
    card.ease = Math.max(1.3, card.ease + 0.1);
  }
  card.nextReview = new Date(Date.now() + card.interval * 24 * 60 * 60 * 1000).toISOString();
  markChanged(currentChar);
}

// -------------------- Speech synthesis helpers --------------------
let englishVoice = null;

function loadEnglishVoice(lang = 'en-US') {
  const voices = speechSynthesis.getVoices();
  englishVoice = voices.find(v => v.lang.startsWith(lang)) || null;
}

speechSynthesis.onvoiceschanged = () => loadEnglishVoice('en-US');

function speak(text, onend) {
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  if (englishVoice) utterance.voice = englishVoice;
  if (onend) utterance.onend = onend;
  window.speechSynthesis.speak(utterance);
}

async function getNextAudio(sentence) {
  const cleaned = sentence.replace(/\(.*?\)/g, '').trim();
  const utterance = new SpeechSynthesisUtterance(cleaned);
  utterance.lang = 'en-US';
  if (englishVoice) utterance.voice = englishVoice;
  speechSynthesis.speak(utterance);

  return new Promise(resolve => {
    utterance.onend = resolve;
  });
}

// ---------- Button helpers ----------
function setSkipButton(enabled) {
  const btn = document.getElementById('skip-btn');
  btn.disabled = !enabled;
}

// FIXME: add a button to mark the last or current character


// ---------- Plural helpers ----------
function guessPlurals(word) {
  const guesses = new Set();
  const lower = word.toLowerCase();

  // Always add plain "s"
  guesses.add(word + "s");

  // Rule: words ending in s, x, z, ch, sh → add "es"
  if (/(s|x|z|ch|sh)$/.test(lower)) {
    guesses.add(word + "es");
  }

  // Rule: words ending in consonant + y → drop y, add "ies"
  if (/[^aeiou]y$/.test(lower)) {
    guesses.add(word.slice(0, -1) + "ies");
  }

  // Rule: words ending in f/fe → ves
  if (/fe?$/.test(lower)) {
    guesses.add(word.replace(/fe?$/, "ves"));
  }

  // Limit to at most 3 guesses
  return Array.from(guesses).slice(0, 3);
}

function extendWithPlurals(words) {
  const extended = new Set(words); // keep originals
  for (const word of words) {
    for (const plural of guessPlurals(word)) {
      extended.add(plural);
    }
  }
  return Array.from(extended);
}

// -------------------- Quiz flow --------------------
async function askQuestion() {
  document.getElementById('result').innerText = 'Listening...';
  document.getElementById('transcript').innerText = '';
  const questionText = `What are the components of '${currentChar}'?`;
  document.getElementById('question').innerText = questionText;
  await getNextAudio(questionText);
  setSkipButton(true);
  const shouldRemove = await listenForComponents();
  setSkipButton(false);
  return shouldRemove;
}

export async function startQuiz() {
  console.log('Starting quiz...');
  await loadDatabase();
  initSheduling(); //obsolte until new characters are added
  initDatabase();
  await updateDueCards()
  let remaining = characters.filter(
    c => database[c].isDue &&
         database[c].isActive &&
         database[c].isHanzi &&
         database[c].expanded_components.flat().length > 1
  );

  let batch = remaining.slice(0,Math.min(10,remaining.length))
  while (batch.length > 0) {
    currentChar = batch[Math.floor(Math.random() * batch.length)];
    const toRemove = await askQuestion();
    markChanged(currentChar);
    if (toRemove) {
      batch = batch.filter(c => c !== currentChar);
    }
  }

  document.getElementById('question').innerText = 'Quiz complete!';
  speak('Batch complete!');

  await updateQuizStatus();

  try {
    await saveChanges();
    console.log("Changes saved successfully.");
    await getNextAudio("Data saved!");
  } catch (err) {
    console.error("Error saving changes:", err);
  }

  if (remaining.length > 10) {
    speak("Do you want to continue with the next batch?");
    const nextBatch = await listenForYesOrNo(20000);
    if (nextBatch) {
      await startQuiz();
    }
  }
  speak("Quiz complete!");
  //saveAll();
}

// -------------------- Recognition helpers --------------------
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;
recognition.continuous = true;

function listenForComponents() {
  return new Promise(resolve => {
    const skipBtn = document.getElementById('skip-btn');
    let settled = false;

    // finalizer to cleanup and resolve
    function finish(result) {
      if (settled) return;
      settled = true;
      if (skipBtn) skipBtn.removeEventListener('click', onSkip);
      recognition.onresult = null;
      recognition.onend = null;
      try { recognition.stop(); } catch (e) {}
      resolve(result);
    }

    // voice result handler (async allowed)
    async function onResult(event) {
      if (settled) return;

      const transcript = (event.results && event.results[0] && event.results[0][0] && event.results[0][0].transcript)
        ? event.results[0][0].transcript.toLowerCase().trim()
        : '';

      if (!transcript) {
        // if empty, try a quick restart
        try { recognition.stop(); } catch (e) {}
        setTimeout(() => { if (!settled && recognition.isActive) recognition.start(); }, 100);
        return;
      }

      // voice skip
      if (transcript.includes('skip')) {
        database[currentChar].skipped = true;
        markChanged(currentChar);
        finish(true);
        return;
      }

      // show transcript immediately
      document.getElementById('transcript').innerText = `You said: "${transcript}"`;

      // stop recognition now, so it doesn't capture while we process
      try { recognition.onend = null; recognition.onresult = null; recognition.stop(); } catch (e) {}

      const words = transcript.split(/,?\s+/);
      const isCorrect = await checkAnswer(words);

      document.getElementById('character-display').textContent = database[currentChar].hanzi;
      if (isCorrect){
        await processAnswer(currentChar, true);
      }
      else{
        await processAnswer(currentChar, false);
      }
      finish(isCorrect);
    }

    // skip button handler (cancels TTS too)
    function onSkip() {
      window.speechSynthesis.cancel();
      if (currentChar && database[currentChar]) {
        database[currentChar].skipped = true;
        markChanged(currentChar);
      }
      finish(true);
    }

    // onend: if recognition stops unexpectedly, restart unless we're settled
    recognition.onresult = onResult;
    recognition.onend = function () {
      if (!settled) recognition.start();
    };

    if (skipBtn) skipBtn.addEventListener('click', onSkip);
    try {
      recognition.start();
    } catch (err) {
      console.error('Could not start recognition', err);
      finish(false);
    }
  });
}

function hasYes(transcript) {
  const keywords = ["yes", "yeah", "yep", "yup", "sure", "ok", "correct"];
  if (keywords.some(word => transcript.toLowerCase().includes(word))) {
    return true;
  }
  return false;
}

// ---------- listenForYesOrNo with 5s fallback ----------
function listenForYesOrNo(time = 5000) {
  return new Promise(resolve => {
    let settled = false;

    // 5 sec fallback -> 'no'
    const timeoutId = setTimeout(() => {
      if (!settled) {
        settled = true;
        try { recognition.stop(); } catch (e) {}
        resolve(false);
      }
    }, time);

    function cleanup() {
      clearTimeout(timeoutId);
      recognition.onresult = null;
      recognition.onend = null;
    }

    recognition.onresult = async function (event) {
      if (settled) return;
      settled = true;
      cleanup();
      const transcript = (event.results && event.results[0] && event.results[0][0] && event.results[0][0].transcript)
        ? event.results[0][0].transcript.toLowerCase().trim()
        : '';
      try { recognition.stop(); } catch (e) {}
      if (!transcript) {
        resolve(false);
        return;
      }
      document.getElementById('transcript').innerText = `You said: "${transcript}"`;
      resolve(hasYes(transcript));
    };

    recognition.onend = function () {
      if (!settled) recognition.start();
    };

    try { recognition.start(); } catch (e) { console.error('Recognition start failed:', e); resolve('no'); }
  });
}

// -------------------- Answer checking --------------------
function remove_a_from_b(a, b, remember_match = false) {
  let needed = [...b];
  let matches = [];

  const stripPunct = str => str.replace(/[.,!?;:]/g, '').toLowerCase();

  for (let comboLen = a.length; comboLen >= 1; comboLen--) {
    for (let start = 0; start <= a.length - comboLen; start++) {
      const combo = stripPunct(a.slice(start, start + comboLen).join(' '));
      for (let i = 0; i < needed.length; i++) {
        if (combo === stripPunct(needed[i])) {
          if (remember_match) matches.push([combo, needed[i]]);
          needed.splice(i, 1);
          break;
        }
      }
    }
  }
  return remember_match ? [needed, matches] : needed;
}

function get_possible_answers(currentChar) {
  function getAllNames(name) {
    let names = [name];
    if (database[name] && Array.isArray(database[name].Aliases)) {
      names = names.concat(database[name].Aliases);
    }
    names = extendWithPlurals(names);
    return names;
  }

  function expandComponentList(list) {
    const options = list.map(getAllNames);
    return options.reduce((a, b) => a.flatMap(d => b.map(e => d.concat([e]))), [[]]);
  }

  let correctSets = [];
  database[currentChar].expanded_components.forEach(set => {
    correctSets = correctSets.concat(expandComponentList(set));
  });
  return correctSets;
}

async function checkAnswer(userWords) {
  const correctSets = get_possible_answers(currentChar);
    database[currentChar].isFalseNegative = false;

  for (const set of correctSets) {
    if (remove_a_from_b(userWords, set).length === 0) {
      document.getElementById('result').innerText = '✅ Correct!';
      await getNextAudio('Correct!');
      return true;
    }
  }

  if (secondaryCheck(userWords)) {
    document.getElementById('result').innerText = '✅ Secondary match found!';
    await getNextAudio('Correct!');
    return true;
  }

  document.getElementById('result').innerText = `❌ \"${userWords.join(' ')}\" is incorrect. The correct answer is: ${correctSets[0].join(' ')}`;
  document.getElementById('character-display').textContent = database[currentChar].hanzi;

  await getNextAudio(`You said: ${userWords.join(', ')}. The correct answer is: ${correctSets[0].join(', and ')}. Were you correct?`);
  recognition.stop();

  const answer = await listenForYesOrNo();
  console.log(answer)
  if (answer == true) {
    database[currentChar].isFalseNegative = true;
    database[currentChar].falseNegativeAnswer = userWords;
    return true;
  }
  return false;
}

function secondaryCheck(userWords) {
  const correctSets = get_possible_answers(currentChar);
  const inputCodes = userWords.map(word => doubleMetaphone(word)).flat();

  for (let set of correctSets) {
    set = set.map(word => doubleMetaphone(word)[0]);
    const [missing] = remove_a_from_b(inputCodes, set, true);
    if (missing.length === 0) return true;
  }
  return false;
}
