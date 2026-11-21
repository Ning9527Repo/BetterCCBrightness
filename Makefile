TARGET := iphone:clang:latest:14.0
INSTALL_TARGET_PROCESSES = SpringBoard

ARCHS = arm64e

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = BetterCCBrightness

$(TWEAK_NAME)_FILES = Tweak.x $(wildcard Masonry/Masonry/*.m)
$(TWEAK_NAME)_LIBRARIES = Accessibility
$(TWEAK_NAME)_FRAMEWORKS = MediaAccessibility
# ControlCenterUIKit / CoreBrightness / BackBoardServices and friends are
# private frameworks that ship inside the dyld shared cache, so they are not
# linkable from the SDK. Resolve every private symbol at runtime instead.
$(TWEAK_NAME)_LDFLAGS = -Wl,-undefined,dynamic_lookup
$(TWEAK_NAME)_CFLAGS = -fobjc-arc -Iinclude -IMasonry -IMasonry/Masonry \
	-Wno-objc-dictionary-duplicate-keys -Wno-missing-noescape

include $(THEOS_MAKE_PATH)/tweak.mk
