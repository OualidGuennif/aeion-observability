# Agora on React Native

The forum's front, on React Native 0.88.1 through Expo SDK 58, in TypeScript. Three screens and one
client:

| File | What it does |
| --- | --- |
| `App.tsx` | Routes between threads, session and compose; owns the session and the status line |
| `src/api.ts` | The whole network contract: health, threads, settings, register, login, logout, cookie |
| `src/screens/ThreadsScreen.tsx` | The list, readable without an account |
| `src/screens/SessionScreen.tsx` | Sign in, create the first account, or sign out |
| `src/screens/ComposeScreen.tsx` | Write a thread; a guest is sent to the session screen |
| `scripts/smoke.mjs` | Drives the compiled client against a live forum |

The same client runs in a browser through `react-native-web`: the forum is then reachable without a
simulator or a phone, which is how it is shown and checked here.

## Run it

```sh
cd demo/forum-mobile
npm install                       # 463 packages

# a forum to talk to, from demo/forum-app
AEION_SQLITE_PATH=/tmp/agora.db AGORA_SESSION_SECRET=<at least 32 bytes> \
  java -jar build/quarkus-app/quarkus-run.jar

npm start                         # Expo dev server; a simulator or a phone on the same network
EXPO_PUBLIC_AGORA_API=http://192.168.1.20:8081 npm start   # reach a forum on another host

npx expo start --port 8082        # the web face, at http://127.0.0.1:8082
```

The API base defaults to `http://127.0.0.1:8081`. On a physical device that address is the phone, not
your machine, so set `EXPO_PUBLIC_AGORA_API` to a reachable one. In a browser keep the host name the
same as the API's (`127.0.0.1`, not `localhost`): the session cookie is `SameSite=Strict`, so the two
must be the same site, and the forum allows only `http://127.0.0.1:8082` and `http://localhost:8082`
with credentials (`quarkus.http.cors.*` in the forum's `application.properties`).

## What was verified, and how

| Claim | Command | Result |
| --- | --- | --- |
| Types are sound | `npx tsc --noEmit` | exit 0 |
| It bundles for a device | `EXPO_NO_TELEMETRY=1 npx expo export --platform ios` | `iOS Bundled 5282ms index.ts (619 modules)`, 1.6 MB Hermes bundle |
| It renders in a browser | `npx expo start --port 8082`, then headless Chrome on `http://127.0.0.1:8082` | the thread list drawn with the real guest list, footer `release unreleased · runtime 25.0.4` read from `/healthz` |
| The browser may write | `curl` from `Origin: http://127.0.0.1:8082` | preflight 200 with `access-control-allow-credentials: true`; register 201, login 200 (CORS header + `Set-Cookie`), create 201 with the CSRF token, **403 without it** |
| The client works against the real forum | `npm run smoke` | 12 steps passed: health, guest list, register, login (87-char signed cookie + 43-char CSRF token), create, read back, list contains it, 401 without a session, 401 on a wrong password, **403 without the CSRF token**, logout, 401 after revocation |

## What was not verified

- **No human on a screen.** The browser build was rendered headlessly and screenshotted; no gesture,
  focus state or layout was inspected by eye. Expo Go was installed on a booted iPhone 17 simulator
  and the project was handed to it, but this Xcode ships no `Simulator.app`, so nothing was seen
  there at all. Treat the UI as unverified.
- **No UI test.** There is no Jest or Testing Library suite; the screens are covered only by the
  typechecker and the bundler.
- **The session is in memory only.** Closing the app signs you out. That is deliberate: a
  fifteen-minute session does not need to survive a restart, and a bearer value persisted on a phone
  is how a demo becomes a finding.
- **Reading a thread** navigates nowhere yet: `onOpen` is intentionally inert, so the list and the
  detail endpoint are proven by the smoke test rather than by a screen.

## Design notes

- **No navigation library.** Three screens managed by one `useState` do not justify
  `@react-navigation` and its dependencies; the route is a string.
- **The cookie is read explicitly, except in a browser.** React Native does not expose `Set-Cookie`
  consistently across platforms, so the client parses the login response and sends
  `Cookie: agora_session=...` itself. A browser hides `Set-Cookie` and forbids `Cookie`, so there the
  fetch uses `credentials: 'include'` and the jar owns the session; the CSRF token comes from the
  login body in both cases.
- **Every mutation carries the CSRF token** the login returned, in `X-CSRF-Token`: holding the cookie
  alone is refused with 403 (feature 006).
- **Two planes stay separate.** The app never sends a worker's `aeion_...` gateway session. Those
  describe a build, not a person, and the API refuses them like any other unknown cookie.
