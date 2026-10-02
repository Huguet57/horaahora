# The Xcode configuration of the iOS builds: Debug or Release.
CONFIGURATION ?= Release

IOS_DERIVED_DATA := build/ios
GRADLE := cd android && ./gradlew $(GRADLE_FLAGS)

.PHONY: deploy-testflight play-bundle ios-build android-build android-lint android-install

# Uploads the app to TestFlight; see scripts/deploy-testflight.sh.
deploy-testflight:
	./scripts/deploy-testflight.sh $(ARGS)

# Builds the signed Google Play bundle of the app; see scripts/build-play-bundle.sh.
play-bundle:
	./scripts/build-play-bundle.sh $(ARGS)

# An unsigned build of the app for a generic iPhone.
ios-build:
	xcodebuild build \
		-project HoraAHoraApp/HoraAHoraApp.xcodeproj \
		-scheme HoraAHoraApp \
		-configuration $(CONFIGURATION) \
		-destination 'generic/platform=iOS' \
		-derivedDataPath $(IOS_DERIVED_DATA) \
		CODE_SIGNING_ALLOWED=NO

# The debug and release APKs of the app.
android-build:
	$(GRADLE) :app:assembleDebug :app:assembleRelease

android-lint:
	$(GRADLE) :app:lintDebug

# Installs the debug app on the connected device or emulator.
android-install:
	$(GRADLE) :app:installDebug
