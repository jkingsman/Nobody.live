const SETTINGS = {
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

function getStoredSetting(settingKey, parse = false) {
  // check that we know about the setting
  if (!SETTINGS[settingKey]) {
    console.error(`Unknown key! ${settingKey} is not one of ${Object.keys(SETTINGS).join(', ')}`);
    return null;
  }

  const requestedSetting = SETTINGS[settingKey];

  // check if we have a stored value
  if (localStorage.getItem(settingKey) === null) {
    // key doesn't exist
    localStorage.setItem(settingKey, requestedSetting.default);
  }

  let rawSetting;
  if (requestedSetting.respectsRememberSetting) {
    if (JSON.parse(localStorage.getItem('shouldRemember')) || false) {
      // this respects the remember setting, and we should use the remembered value
      rawSetting = localStorage.getItem(settingKey);
    } else {
      // this respects the remember setting, but we are not set to remember right now
      // give the default
      return requestedSetting.default;
    }
  } else {
    // doesn't respect remember setting; provide what's in storage
    rawSetting = localStorage.getItem(settingKey);
  }

  if (parse) {
    try {
      return JSON.parse(rawSetting);
    } catch (error) {
      console.error(`Parse failure! Could not parse key '${settingKey}' with value '${rawSetting}'.`);
      return rawSetting;
    }
  } else {
    return rawSetting;
  }
}

function setStoredSetting(settingsObj) {
  localStorage.setItem('storageVersion', '0.0.1');
  for (const [settingKey, value] of Object.entries(settingsObj)) {
    // check that we know about the setting
    if (!SETTINGS[settingKey]) {
      console.error(`Unknown key! ${settingKey} is not one of ${Object.keys(SETTINGS).join(', ')}`);
      return;
    }

    const requestedSetting = SETTINGS[settingKey];
    if (requestedSetting.allowedValues && !requestedSetting.allowedValues.includes(value)) {
      console.error(`Illegal value! '${value}' is not one of ${requestedSetting.allowedValues.join(', ')}`);
      return;
    }

    const shouldRemember = JSON.parse(localStorage.getItem('shouldRemember')) || false;
    if (requestedSetting.respectsRememberSetting) {
      if (shouldRemember) {
        // this respects the remember setting, and we should set the remembered value
        localStorage.setItem(settingKey, value);
      } else {
        // this respects the remember setting, but we are not set to remember right now so store default
        localStorage.setItem(settingKey, requestedSetting.default);
      }
    } else {
      // doesn't respect remember setting; store what we're given
      localStorage.setItem(settingKey, value);
    }
  }
}

// migrate from older storage engine versions
function migrateData() {
  const shouldMigrate = localStorage.getItem('streamHistoryJSON') && !localStorage.getItem('hasMigrated');
  if (shouldMigrate) {
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
      console.error("Migration has failed!")
      console.error(error);
    }

    localStorage.clear();
    setStoredSetting(settingsObj);
    localStorage.setItem('hasMigrated', true);
  }
}
