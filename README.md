# Hanzi-Network-Quiz

Fully voice controllable Quiz app for learning the components of Chinese Characters. I built it to study Simplified Chinese using the books by James Heisigs: "Remembering Simplified Hanzi 1&2", but it could theoretically be adjusted to study other Data, that can be represented as a network

## Progress

The app is still in development. Missing features include:

- Finalization of the Database

- Implementation of a more sophisticated scheduling system

- Pausing and interrupting Quiz

- Polishing of the interface



## Database

The Database containing the Characters and there relationship is based on the shared Anki Deck: [James W. Heisig - Remembering Simplified Hanzi 1 & 2 ](https://ankiweb.net/shared/info/1627669267)
The final Database.json was extended by including the components of the radicals and adding Aliases for the radicals as they are used in Heisigs Books.

## Compatability

The app uses the [Speech Recognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition ) feature of Google Chrome. It is thus not compatible with other browsers that dont have acces to this feature.

## Usage

The App is launched using [Node](https://nodejs.org/en)

```properties
node server.js
```

to create a webpage, which will be hosted on the local Network.

The current setup also requires the generation of local certificates. This can be done using [mkcert](https://github.com/FiloSottile/mkcert/releases?utm_source=chatgpt.com).


