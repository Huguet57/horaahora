"""The public and internal builds of the apps, and the checks that keep them apart.

The public app, the one in the App Store and on Google Play, has the calculator, the score table
and their settings. The internal app is a separate development app, with its own identifier and
name: it adds Hora a Hora, Agenda, their settings and the news notifications. The build profile,
CASTELLS_BUILD_PROFILE=public|internal, chooses which one a build produces; `public` is the
default.

- `profiles` defines both profiles and what only the internal app may contain.
- `xcode_project`, `swift_package` and `gradle_build` read the Xcode project, the Swift package
  and the Gradle build, so the tests can check that no internal module or entry point reaches
  the public app.
- `android_inspection` and `ios_inspection` inspect built apps. CI runs them after building each
  profile (see the Makefile):

      python3 -m scripts.app_profiles android public
      python3 -m scripts.app_profiles ios public --app build/ios/.../HoraAHoraApp.app

Only the standard library is used, so the inspection also runs on the macOS CI runners.
"""
