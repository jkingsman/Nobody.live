/* eslint-disable no-console */
// eslint-disable-next-line no-unused-vars
class Settings {
  constructor() {
    this.KNOWN_SETTINGS = {
      shouldRemember: {
        respectsRememberSetting: false,
        default: false,
        allowedValues: [true, false],
      },
      include: {
        respectsRememberSetting: true,
        default: '',
      },
      exclude: {
        respectsRememberSetting: true,
        default: '',
      },
      minDuration: {
        respectsRememberSetting: true,
        default: 0,
        allowedValues: [0, 3, 5, 10],
      },
      maxViewers: {
        respectsRememberSetting: true,
        default: 0,
        allowedValues: [0, 1],
      },
      searchOperator: {
        respectsRememberSetting: true,
        default: 'all',
        allowedValues: ['all', 'any'],
      },
      widePage: {
        respectsRememberSetting: false,
        default: false,
        allowedValues: [true, false],
      },
      minimalPage: {
        respectsRememberSetting: false,
        default: false,
        allowedValues: [true, false],
      },
      dualColumn: {
        respectsRememberSetting: false,
        default: false,
        allowedValues: [true, false],
      },
      texturedBackground: {
        respectsRememberSetting: false,
        default: false,
        allowedValues: [true, false],
      },
      streamHistory: {
        respectsRememberSetting: false,
        default: '[]',
      },
    };

    this.ephemeral = {
      numberOfThumbnailsToFetch: 16,
      server: document.location.origin,
      currentStream: null,
    };

    this.debug_enabled = false;
  }

  static shouldRemember() {
    return JSON.parse(localStorage.getItem('shouldRemember')) || false;
  }

  setBulk(settingsObj) {
    for (const [key, value] of Object.entries(settingsObj)) {
      this.set(key, value);
    }
  }

  set(key, value) {
    // if we haven't heard of it, set it ephemerally
    if (!this.KNOWN_SETTINGS[key]) {
      this.ephemeral[key] = value;
      return;
    }

    const requestedSetting = this.KNOWN_SETTINGS[key];
    if (requestedSetting.allowedValues && !requestedSetting.allowedValues.includes(value)) {
      console.error(`Illegal value! Key '${key}' has value '${value}' is not one of \
${requestedSetting.allowedValues.join(', ')}`);
      return;
    }

    if (requestedSetting.respectsRememberSetting) {
      if (this.constructor.shouldRemember()) {
        // this respects the remember setting, and we should set the remembered value
        localStorage.setItem(key, value);
      } else {
        // we are not remembering right now so store default long term and set it in ephemeral]
        localStorage.setItem(key, requestedSetting.default);
        this.ephemeral[key] = value;
      }
    } else {
      // doesn't respect remember setting; store what we're given
      localStorage.setItem(key, value);
    }
  }

  get(key, parse = false, defaultValue = null) {
    let rawSetting;
    // this is such a mess; sorry
    // if it's not a known key, check for it as an ephemeral key
    // if we still don't have it, return the default or error out with null
    if (!this.KNOWN_SETTINGS[key]) {
      // if we haven't heard of it, get it ephemerally
      if (!this.ephemeral[key]) {
        if (defaultValue) {
          return defaultValue;
        }

        console.error(`Unknown key! ${key} is not one of ${Object.keys(this.KNOWN_SETTINGS).join(', ')} nor found in ephemera.`);
        return null;
      }

      rawSetting = this.ephemeral[key];
    } else {
      const requestedSetting = this.KNOWN_SETTINGS[key];
      if (requestedSetting.respectsRememberSetting) {
        if (this.constructor.shouldRemember()) {
          // this setting respects remember and remember is set; return from storage
          rawSetting = localStorage.getItem(key);
        } else {
          // this setting respects remember and but remember is not set; try for ephemeral or default
          rawSetting = this.ephemeral[key];
          if (!rawSetting) {
            // we don't have this stored; return default
            rawSetting = requestedSetting.default;
          }
        }
      } else {
        // does not respect remembering; return from localstorage
        rawSetting = localStorage.getItem(key);
        if (!rawSetting) {
          // we don't have this stored; return default
          rawSetting = requestedSetting.default;
        }
      }
    }

    if (parse) {
      try {
        return JSON.parse(rawSetting);
      } catch (error) {
        console.error(`Parse failure! Could not parse key '${key}' with value '${rawSetting}'.`);
        return rawSetting;
      }
    } else {
      return rawSetting;
    }
  }
}
