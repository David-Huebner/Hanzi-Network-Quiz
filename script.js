import {doubleMetaphone} from 'https://esm.sh/double-metaphone@2?bundle'


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

// At the end of the quiz:
async function saveChanges() {
  for (const key of changedKeys) {
    await updateDatabaseEntry(key, database[key]);
  }
}

async function updateQuizStatus() {
    // Get today's date in YYYY-MM-DD format
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    await fetch('/api/quiz-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lastCompleted: today })
    });
}

// Speech synthesis helper
function speak(text, onend) {
    window.speechSynthesis.cancel(); // Stop any ongoing speech
    const utterance = new window.SpeechSynthesisUtterance(text);
    if (onend) {
        utterance.onend = onend;
    }
    window.speechSynthesis.speak(utterance);
}

// Speech synthesis helper 2
async function getNextAudio(sentence) {
      let audio = new SpeechSynthesisUtterance(sentence);
      window.speechSynthesis.speak(audio);

      return new Promise(resolve => {
        audio.onend = resolve;
      });
}

let database = {};
let characters = [];
let currentChar = null;
let changedKeys = [];

async function askQuestion() {
    let toRemove = false;
    document.getElementById("result").innerText = "Listening...";
    document.getElementById("transcript").innerText = "";
    const questionText = `What are the components of '${currentChar}'?`;
    document.getElementById("question").innerText = questionText;
    await getNextAudio(questionText);
    toRemove = await listenForComponents();
    return toRemove;
}

export async function startQuiz() {
    console.log("Starting quiz...");
    await loadDatabase()
    console.log("Loaded characters:", characters);
    let remaining = characters.filter(c => database[c].isDue && database[c].isActive);
    let toRemove = false;
    while (remaining.length > 0) {
        currentChar = remaining[Math.floor(Math.random() * remaining.length)];
        toRemove = await askQuestion();
        markChanged(currentChar);
        database[currentChar].wasSkipped = false;
        console.log("toRemove:", toRemove);
        if (toRemove) {
            remaining = remaining.filter(c => c !== currentChar);
    }
    }
    document.getElementById("question").innerText = "Quiz complete!";
    speak("Quiz complete!");
    updateQuizStatus()
    saveChanges().then(() => {
        console.log("Changes saved successfully.");
        speak("Data saved!");
    }).catch(err => {
        console.error("Error saving changes:", err);
    });
    return;
}



const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;
recognition.continuous = true;

// // Add debugging logs
// recognition.onstart = function() {
//     console.log("Speech recognition started");
// };
// recognition.onend = function() {
//     console.log("Speech recognition ended");
// };

// recognition.onerror = function(event) {
//     document.getElementById("result").innerText = `Error: ${event.error}`;
// };


function stopRecognitionAsync(recognition) {
    return new Promise(resolve => {
        recognition.onend = resolve;
        recognition.stop();
    });
}


function listenForComponents() {
    return new Promise(resolve => {
        recognition.interimResults = false;
        recognition.onresult = async function(event) {
            answered = true;
            console.log("Speech recognition result received", event);
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            recognition.stop();
            if (transcript == "") {
                console.log("Empty transcript, ignoring.");
                await stopRecognitionAsync(recognition);
                recognition.start();
                console.log("Restarting");
                return; // Do not stop or resolve if transcript is empty                
            }
            else {
                document.getElementById("transcript").innerText = `You said: "${transcript}"`;
                if (transcript.includes("skip")) {
                    console.log("Skip command detected, stopping recognition.");
                    database[currentChar].skipped = true;
                    database[currentChar].dueIn = 0; // Reset dueIn to 0
                    resolve(true); // remove from the quit
                }
                else {
                const isCorrect = await checkAnswer(transcript.split(/,?\s+/));
                if (isCorrect) {
                    database[currentChar].dueIn = database[currentChar].dueIn*2
                }
                else {
                    database[currentChar].dueIn = 0; // Reset dueIn to 0
                }
                resolve(isCorrect);
                }
            }
        };
        recognition.onend = function() {
            if (!answered) {
                console.log("Recognition ended without answer, restarting...");
                recognition.start();
            }
        };
    let answered = false;
    console.log("Starting speech recognition for components...");
    recognition.start();
    console.log("Started");

    });
}

function getYesNoAnswer(transcript) {
  // Accepted synonyms → normalize them
  if (["yes", "yeah", "yep", "yup", "sure", "ok"].includes(transcript)) {
    return "yes";
  }
  if (["no", "nope", "nah"].includes(transcript)) {
    return "no";
  }

  // Not recognized as yes/no
  return null;
}

function listenForYesOrNo() {
    return new Promise(resolve => {
        recognition.interimResults = true;
        recognition.onresult = async function(event) {
            answered = true;
            console.log("Speech recognition result received", event);
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            recognition.stop();
            if (transcript == "") {
                console.log("Empty transcript, ignoring.");
                await stopRecognitionAsync(recognition);
                recognition.start();
                console.log("Restarting");
                return; // Do not stop or resolve if transcript is empty                
            }
            else {
                document.getElementById("transcript").innerText = `You said: "${transcript}"`;
                let answer = getYesNoAnswer(transcript);
                recognition.stop(); // Stop listening after processing
                if (answer == null) {
                    answer = "no";
                }
                resolve(answer);
            }
        };
        recognition.onend = function() {
            if (!answered) {
                console.log("Recognition ended without answer, restarting...");
                recognition.start();
            }
        };
        let answered = false;
        recognition.start();
    });
}

function remove_a_from_b(a, b, remember_match = false) {
    // Make a copy of the set to track needed components
    let needed = [...b];
    let matches = [];

    // Helper to remove all punctuation from a string
    function stripPunct(str) {
        return (str.replace(/[.,!?;:]/g, '')).toLowerCase();
    }

    // Try all possible contiguous combinations of elements in a
    for (let comboLen = a.length; comboLen >= 1; comboLen--) {
        for (let start = 0; start <= a.length - comboLen; start++) {
            // Join the combo with spaces and strip punctuation
            const combo = stripPunct(a.slice(start, start + comboLen).join(' '));
            // Try to match with each needed component (also strip punctuation)
            for (let i = 0; i < needed.length; i++) {
                const neededStripped = stripPunct(needed[i]);
                if (combo === neededStripped) { 
                    if (remember_match) {
                        matches.push([combo,needed[i]]);
                    }
                    needed.splice(i, 1);
                    break;
                }
            }
        }
    }
    if (remember_match) {
        return [needed,matches];
    }
    else {
        return needed;
    }
}

function get_possible_answers(currentChar) {
    // Helper to get all possible names for a component (original + aliases)
    function getAllNames(name) {
        let names = [name];
        if (database[name] && Array.isArray(database[name].Aliases)) {
            names = names.concat(database[name].Aliases);
        }
        return names;
    }
    // Generate all possible lists with aliases substituted
    function expandComponentList(list) {
        // For each element, get all possible names
        const options = list.map(getAllNames);
        // Cartesian product to get all combinations
        function cartesian(arr) {
            return arr.reduce((a, b) => a.flatMap(d => b.map(e => d.concat([e]))), [[]]);
        }
        return cartesian(options);
    }
    // Expand all component sets
    let correctSets = [];
    database[currentChar].components.forEach(set => {
        correctSets = correctSets.concat(expandComponentList(set));
    });
    return correctSets
}

async function checkAnswer(userWords) {
    let answer = "no";
    console.log("Checking answer for:", userWords);
    const correctSets = get_possible_answers(currentChar);
    let primaryMatch = false;
    let secondaryMatch = false;
    console.log("Correct sets:", correctSets);
    for (const set of correctSets) {
        const missing = remove_a_from_b(userWords, set);
        if (missing.length === 0) {
            primaryMatch = true;
            break;
        }
    }
    if (primaryMatch) {
        console.log("correct", userWords);
        document.getElementById("result").innerText = "✅ Correct!";
        await getNextAudio("Correct!");
        return true;
    }
    secondaryMatch = secondaryCheck(userWords);
    if (secondaryMatch) {
        console.log("secondary match", userWords);
        document.getElementById("result").innerText = "✅ Secondary match found!";
        await getNextAudio("Correct!");
        return true;
    }
    // If no matches, show incorrect message
    console.log("wrong", userWords);
    // Wrong answer: repeat, say wrong, ask again, offer skip
    document.getElementById("result").innerText = `❌ \"${userWords.join(' ')}\" is incorrect. The correct answer is: ${correctSets[0].join(' ')}`;
    await getNextAudio(`You said: ${userWords.join(', ')}. The correct answer is: ${correctSets[0].join(', and ')}. Were you correct?`);
    recognition.stop();
    answer = await listenForYesOrNo();
    if (answer == "yes") {
        database[currentChar].isFalseNegative = true;
        database[currentChar].falseNegativeAnswer = userWords; 
        return true
    }
    return false;
}

function secondaryCheck(userWords) {
    const correctSets = get_possible_answers(currentChar);
    let secondaryMatch = false;
    let inputCodes = userWords.map(word => doubleMetaphone(word));
    inputCodes = inputCodes.flat();
    for (let set of correctSets) {
        // console.log(`Checking secondary matches for: ${set}`);
        set = set.map(word => doubleMetaphone(word));
        set = set.map(double => double[0]);
        // console.log(inputCodes,set);
        const [missing, matches] = remove_a_from_b(inputCodes, set, true);
        if (missing.length === 0) {
            // console.log(`Secondary match found: ${matches}`);
            secondaryMatch = true;
            for (const match of matches) {
                // console.log(`Secondary match found: ${match[0]} matches ${match[1]}`);
            }
            return secondaryMatch;
        }
    }
    return secondaryMatch;
}
