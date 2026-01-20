const BasicSettings = {
    currentSettings: {},
    availableTimezones: [],
    availableLocales: [],

    init: function () {
        console.log("Initializing Basic Settings");
        this.loadSettings();
        this.loadAvailableOptions();
        this.setupEventListeners();
    },

    loadSettings: function () {
        callDBus("GetBasicSettings")
            .done(function (settings) {
                BasicSettings.currentSettings = settings;
                BasicSettings.populateForm(settings);
                console.log("Basic settings loaded:", settings);
            })
            .fail(function (error) {
                console.error("Failed to load basic settings:", error);
                showNotification("error", "Failed to load basic settings");
            });
    },

    populateForm: function (settings) {
        const hostnameInput = document.getElementById("hostname");
        const timezoneSelect = document.getElementById("timezone");
        const localeSelect = document.getElementById("locale");
        const ntpInput = document.getElementById("ntp-server");

        if (hostnameInput && settings.hostname) {
            hostnameInput.value = settings.hostname;
        }

        if (timezoneSelect && settings.timezone) {
            timezoneSelect.value = settings.timezone;
        }

        if (localeSelect && settings.locale) {
            localeSelect.value = settings.locale;
        }

        if (ntpInput && settings.ntp_server) {
            ntpInput.value = settings.ntp_server;
        }
    },

    loadAvailableOptions: function () {
        this.loadTimezones();
        this.loadLocales();
    },

    loadTimezones: function () {
        callDBus("GetAvailableTimezones")
            .done(function (result) {
                // cockpit.dbus returns method results as an array, extract first element
                var timezones = Array.isArray(result) ? result[0] : result;
                // Handle if it's still a single string with newlines
                if (typeof timezones === 'string') {
                    timezones = timezones.split('\n').filter(function (tz) { return tz.trim() !== ''; });
                }
                // Ensure it's an array
                if (!Array.isArray(timezones)) {
                    timezones = [timezones];
                }
                BasicSettings.availableTimezones = timezones;
                BasicSettings.populateTimezones(timezones);
                console.log("Loaded", timezones.length, "timezones");
            })
            .fail(function (error) {
                console.error("Failed to load timezones:", error);
                showNotification("error", "Failed to load available timezones");
            });
    },

    populateTimezones: function (timezones) {
        const timezoneSelect = document.getElementById("timezone");
        if (!timezoneSelect) return;

        timezoneSelect.innerHTML = "";

        const commonTimezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Shanghai",
            "Asia/Tokyo",
            "Australia/Sydney"
        ];

        commonTimezones.forEach(function (tz) {
            if (timezones.includes(tz)) {
                const option = document.createElement("option");
                option.value = tz;
                option.textContent = tz;
                timezoneSelect.appendChild(option);
            }
        });

        const separator = document.createElement("option");
        separator.disabled = true;
        separator.textContent = "---";
        timezoneSelect.appendChild(separator);

        timezones.sort().forEach(function (tz) {
            if (!commonTimezones.includes(tz)) {
                const option = document.createElement("option");
                option.value = tz;
                option.textContent = tz;
                timezoneSelect.appendChild(option);
            }
        });

        if (BasicSettings.currentSettings.timezone) {
            timezoneSelect.value = BasicSettings.currentSettings.timezone;
        }
    },

    loadLocales: function () {
        callDBus("GetAvailableLocales")
            .done(function (result) {
                // cockpit.dbus returns method results as an array, extract first element
                var locales = Array.isArray(result) ? result[0] : result;
                // Handle if it's still a single string with newlines
                if (typeof locales === 'string') {
                    locales = locales.split('\n').filter(function (loc) { return loc.trim() !== ''; });
                }
                // Ensure it's an array
                if (!Array.isArray(locales)) {
                    locales = [locales];
                }
                BasicSettings.availableLocales = locales;
                BasicSettings.populateLocales(locales);
                console.log("Loaded", locales.length, "locales");
            })
            .fail(function (error) {
                console.error("Failed to load locales:", error);
                showNotification("error", "Failed to load available locales");
            });
    },

    populateLocales: function (locales) {
        const localeSelect = document.getElementById("locale");
        if (!localeSelect) return;

        localeSelect.innerHTML = "";

        const commonLocales = [
            "en_US.utf8",
            "en_GB.utf8",
            "zh_CN.utf8",
            "zh_TW.utf8",
            "ja_JP.utf8",
            "ko_KR.utf8",
            "de_DE.utf8",
            "fr_FR.utf8",
            "es_ES.utf8",
            "C.utf8"
        ];

        locales.forEach(function (locale) {
            const option = document.createElement("option");
            option.value = locale;
            option.textContent = locale;
            localeSelect.appendChild(option);
        });

        if (BasicSettings.currentSettings.locale) {
            localeSelect.value = BasicSettings.currentSettings.locale;
        }
    },

    setupEventListeners: function () {
        const setHostnameBtn = document.getElementById("set-hostname");
        if (setHostnameBtn) {
            setHostnameBtn.addEventListener("click", function () {
                BasicSettings.setHostname();
            });
        }

        const timezoneSelect = document.getElementById("timezone");
        if (timezoneSelect) {
            timezoneSelect.addEventListener("change", function () {
                BasicSettings.setTimezone(this.value);
            });
        }

        const localeSelect = document.getElementById("locale");
        if (localeSelect) {
            localeSelect.addEventListener("change", function () {
                BasicSettings.setLocale(this.value);
            });
        }

        const hostnameInput = document.getElementById("hostname");
        if (hostnameInput) {
            hostnameInput.addEventListener("keypress", function (e) {
                if (e.key === "Enter") {
                    BasicSettings.setHostname();
                }
            });
        }
    },

    setHostname: function () {
        const hostnameInput = document.getElementById("hostname");
        const hostname = hostnameInput.value.trim();

        clearError("hostname");

        const validation = validateHostname(hostname);
        if (!validation.valid) {
            showError("hostname", validation.message);
            return;
        }

        const setHostnameBtn = document.getElementById("set-hostname");
        setHostnameBtn.disabled = true;

        callDBus("SetHostname", [hostname])
            .done(function (success) {
                setHostnameBtn.disabled = false;

                if (success) {
                    showNotification("success", "Hostname changed successfully");
                    BasicSettings.currentSettings.hostname = hostname;
                } else {
                    showNotification("error", "Failed to change hostname");
                }
            })
            .fail(function (error) {
                setHostnameBtn.disabled = false;
                console.error("Failed to set hostname:", error);
                showNotification("error", "Failed to change hostname: " + error.message);
            });
    },

    setTimezone: function (timezone) {
        if (!timezone) {
            return;
        }

        callDBus("SetTimezone", [timezone])
            .done(function (success) {
                if (success) {
                    showNotification("success", "Timezone changed successfully");
                    BasicSettings.currentSettings.timezone = timezone;
                } else {
                    showNotification("error", "Failed to change timezone");
                    BasicSettings.loadSettings();
                }
            })
            .fail(function (error) {
                console.error("Failed to set timezone:", error);
                showNotification("error", "Failed to change timezone: " + error.message);
                BasicSettings.loadSettings();
            });
    },

    setLocale: function (locale) {
        if (!locale) {
            return;
        }

        callDBus("SetLocale", [locale])
            .done(function (success) {
                if (success) {
                    showNotification("success", "Locale changed successfully");
                    BasicSettings.currentSettings.locale = locale;
                } else {
                    showNotification("error", "Failed to change locale");
                    BasicSettings.loadSettings();
                }
            })
            .fail(function (error) {
                console.error("Failed to set locale:", error);
                showNotification("error", "Failed to change locale: " + error.message);
                BasicSettings.loadSettings();
            });
    },

    refresh: function () {
        this.loadSettings();
    }
};
