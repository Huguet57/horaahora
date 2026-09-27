# The app to build: public, the app in the stores (the default), or internal, the separate
# development app that adds Hora a Hora, Agenda, their settings and the news notifications.
CASTELLS_BUILD_PROFILE ?= public
# The Xcode configuration of the iOS builds: Debug or Release.
CONFIGURATION ?= Release

ifeq ($(CASTELLS_BUILD_PROFILE),public)
IOS_SCHEME := HoraAHoraApp
ANDROID_FLAVOR := Public
else ifeq ($(CASTELLS_BUILD_PROFILE),internal)
IOS_SCHEME := HoraAHoraAppInternal
ANDROID_FLAVOR := Internal
else
$(error CASTELLS_BUILD_PROFILE must be public or internal, not "$(CASTELLS_BUILD_PROFILE)")
endif

# Both schemes share it: their apps have different names, and the second build reuses the
# modules the first compiled.
IOS_DERIVED_DATA := build/ios
IOS_APP := $(IOS_DERIVED_DATA)/Build/Products/$(CONFIGURATION)-iphoneos/$(IOS_SCHEME).app
GRADLE := cd android && ./gradlew $(GRADLE_FLAGS) -Pcastells.buildProfile=$(CASTELLS_BUILD_PROFILE)

.PHONY: deploy-testflight ios-build ios-verify android-build android-lint android-verify android-install

# Uploads the public app to TestFlight; see scripts/deploy-testflight.sh.
deploy-testflight:
	./scripts/deploy-testflight.sh $(ARGS)

# An unsigned build of the app for a generic iPhone.
ios-build:
	xcodebuild build \
		-project HoraAHoraApp/HoraAHoraApp.xcodeproj \
		-scheme $(IOS_SCHEME) \
		-configuration $(CONFIGURATION) \
		-destination 'generic/platform=iOS' \
		-derivedDataPath $(IOS_DERIVED_DATA) \
		CODE_SIGNING_ALLOWED=NO

# Checks that the app from ios-build has what its profile allows, and nothing else.
ios-verify:
	python3 -m scripts.app_profiles ios $(CASTELLS_BUILD_PROFILE) --app $(IOS_APP) --configuration $(CONFIGURATION)

# The debug and release APKs of the app.
android-build:
	$(GRADLE) :app:assembleDebug :app:assembleRelease

android-lint:
	$(GRADLE) :app:lint$(ANDROID_FLAVOR)Debug

# Checks that the APKs from android-build have what their profile allows, and nothing else.
android-verify:
	python3 -m scripts.app_profiles android $(CASTELLS_BUILD_PROFILE)

# Installs the debug app on the connected device or emulator.
android-install:
	$(GRADLE) :app:install$(ANDROID_FLAVOR)Debug
