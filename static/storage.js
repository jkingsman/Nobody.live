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

    localStorage.setItem('storageVersion', '0.0.1');
  }

  debug(str) {
    if (this.debug_enabled) {
      console.log(str);
    }
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
      this.debug(`1 Setting ${key} to ephemeral (${value})`);
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
        this.debug(`2 Setting ${key} to localstorage (${value})`);
        localStorage.setItem(key, value);
      } else {
        // we are not remembering right now so store default long term and set it in ephemeral
        this.debug(`3 Setting ${key} to default in local storage and ephemeral to (${value})`);
        localStorage.setItem(key, requestedSetting.default);
        this.ephemeral[key] = value;
      }
    } else {
      // doesn't respect remember setting; store what we're given
      localStorage.setItem(key, value);
      this.debug(`9 Setting ${key} to localstorage (${value})`);
    }
  }

  get(key, parse = false) {
    let rawSetting;
    if (!this.KNOWN_SETTINGS[key]) {
      // if we haven't heard of it, get it ephemerally
      if (!this.ephemeral[key]) {
        console.error(`Unknown key! ${key} is not one of \
${Object.keys(this.KNOWN_SETTINGS).join(', ')} nor found in ephemera.`);
        return null;
      }

      this.debug(`4 Returning ${key} from ephemeral (${this.ephemeral[key]})`);
      rawSetting = this.ephemeral[key];
    } else {
      const requestedSetting = this.KNOWN_SETTINGS[key];
      if (requestedSetting.respectsRememberSetting) {
        if (this.constructor.shouldRemember()) {
          // this setting respects remember and remember is set; return from storage
          rawSetting = localStorage.getItem(key);
          this.debug(`5 Returning ${key} from localstorage (${rawSetting})`);
        } else {
          // this setting respects remember and but remember is not set; try for ephemeral or default
          rawSetting = this.ephemeral[key];
          if (!rawSetting) {
            // we don't have this stored; return default
            rawSetting = requestedSetting.default;
            this.debug(`6 Returning ${key} from default (${rawSetting})`);
          } else {
            this.debug(`7 Returning ${key} from ephemeral (${rawSetting})`);
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

  // migrate from legacy storage versions
  migrateData() {
    const shouldMigrate = localStorage.getItem('streamHistoryJSON') && !localStorage.getItem('hasMigrated');
    if (shouldMigrate) {
      console.log("MIGRATING")
      const settingsObj = {};

      try {
        settingsObj.widePage = JSON.parse(localStorage.getItem('widePage')) || false;
        settingsObj.minimalPage = JSON.parse(localStorage.getItem('minimalPage')) || false;
        settingsObj.streamHistory = JSON.stringify(JSON.parse(localStorage.getItem('streamHistoryJSON')) || []);

        settingsObj.shouldRemember = JSON.parse(localStorage.getItem('streamFilterRemember')) || false;
        if (settingsObj.shouldRemember) {
          settingsObj.include = JSON.parse(localStorage.getItem('streamFilter')).include;
          settingsObj.exclude = JSON.parse(localStorage.getItem('streamFilter')).exclude;
          settingsObj.minDuration = JSON.parse(localStorage.getItem('streamFilter')).minAge;
          settingsObj.maxViewers = JSON.parse(localStorage.getItem('streamFilter')).max_viewers;
          settingsObj.searchOperator = JSON.parse(localStorage.getItem('streamFilter')).search_operator;
        }
      } catch (error) {
        console.error('Migration has failed!');
        console.error(error);
      }

      localStorage.clear();
      this.setBulk(settingsObj);
      localStorage.setItem('hasMigrated', true);
    }
  }
}
