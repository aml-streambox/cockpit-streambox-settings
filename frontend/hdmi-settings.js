/**
 * HDMI Loopout Settings Module
 * Handles HDMI passthrough configuration via streambox-tv
 */

const HdmiSettings = {
    config: {},
    audioDevices: { playback: [], capture: [] },

    init: function () {
        console.log("Initializing HDMI Loopout Settings");
        this.loadAudioDevices();
        this.loadConfig();
        this.setupEventListeners();
    },

    loadAudioDevices: function () {
        callDBus("GetAudioDevices")
            .done(function (result) {
                var devices = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(devices)) {
                    devices = typeof devices[0] === 'string' ? JSON.parse(devices[0]) : devices[0];
                }
                HdmiSettings.audioDevices = devices;
                HdmiSettings.populateAudioDevices(devices);
                console.log("Audio devices loaded:", devices);
            })
            .fail(function (error) {
                console.error("Failed to load audio devices:", error);
            });
    },

    populateAudioDevices: function (devices) {
        var captureSelect = document.getElementById("audio-capture");
        var playbackSelect = document.getElementById("audio-playback");

        if (captureSelect && devices.capture) {
            captureSelect.innerHTML = "";
            devices.capture.forEach(function (dev) {
                var option = document.createElement("option");
                option.value = dev.address;
                option.textContent = dev.address + " - " + dev.name;
                captureSelect.appendChild(option);
            });
            // Add manual option
            var manualOpt = document.createElement("option");
            manualOpt.value = "custom";
            manualOpt.textContent = "Custom...";
            captureSelect.appendChild(manualOpt);
        }

        if (playbackSelect && devices.playback) {
            playbackSelect.innerHTML = "";
            devices.playback.forEach(function (dev) {
                var option = document.createElement("option");
                option.value = dev.address;
                option.textContent = dev.address + " - " + dev.name;
                playbackSelect.appendChild(option);
            });
            var manualOpt = document.createElement("option");
            manualOpt.value = "custom";
            manualOpt.textContent = "Custom...";
            playbackSelect.appendChild(manualOpt);
        }
    },

    loadConfig: function () {
        callDBus("GetHdmiConfig")
            .done(function (result) {
                var config = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(config)) {
                    config = typeof config[0] === 'string' ? JSON.parse(config[0]) : config[0];
                }
                HdmiSettings.config = config;
                HdmiSettings.populateForm(config);
                console.log("HDMI config loaded:", config);
            })
            .fail(function (error) {
                console.error("Failed to load HDMI config:", error);
            });
    },

    populateForm: function (config) {
        var video = config.video || {};
        var audio = config.audio || {};

        // Video settings
        var gameModeSelect = document.getElementById("hdmi-game-mode");
        var vrrModeSelect = document.getElementById("hdmi-vrr-mode");
        var sourceSelect = document.getElementById("hdmi-source");

        if (gameModeSelect) gameModeSelect.value = video.game_mode || 2;
        if (vrrModeSelect) vrrModeSelect.value = video.vrr_mode || 2;
        if (sourceSelect) sourceSelect.value = video.hdmi_source || "HDMI2";

        // Audio settings
        var captureSelect = document.getElementById("audio-capture");
        var playbackSelect = document.getElementById("audio-playback");
        var latencyInput = document.getElementById("audio-latency");
        var channelsSelect = document.getElementById("audio-channels");
        var sampleRateSelect = document.getElementById("audio-sample-rate");
        var audioEnabledCheckbox = document.getElementById("audio-enabled");

        if (captureSelect) {
            captureSelect.value = audio.capture_device || "hw:0,2";
            if (!captureSelect.value || captureSelect.selectedIndex === -1) {
                captureSelect.value = "custom";
                document.getElementById("audio-capture-custom").value = audio.capture_device || "";
                document.getElementById("audio-capture-custom").style.display = "block";
            }
        }
        if (playbackSelect) {
            playbackSelect.value = audio.playback_device || "hw:0,0";
            if (!playbackSelect.value || playbackSelect.selectedIndex === -1) {
                playbackSelect.value = "custom";
                document.getElementById("audio-playback-custom").value = audio.playback_device || "";
                document.getElementById("audio-playback-custom").style.display = "block";
            }
        }
        if (latencyInput) latencyInput.value = audio.latency_us || 10000;
        if (channelsSelect) channelsSelect.value = audio.channels || 2;
        if (sampleRateSelect) sampleRateSelect.value = audio.sample_rate || 48000;
        if (audioEnabledCheckbox) audioEnabledCheckbox.checked = audio.enabled !== false;
    },

    setupEventListeners: function () {
        var self = this;

        var saveBtn = document.getElementById("save-hdmi-config");
        if (saveBtn) {
            saveBtn.addEventListener("click", function () {
                self.saveConfig();
            });
        }

        // Show custom input when "Custom..." is selected
        var captureSelect = document.getElementById("audio-capture");
        var playbackSelect = document.getElementById("audio-playback");

        if (captureSelect) {
            captureSelect.addEventListener("change", function () {
                var customInput = document.getElementById("audio-capture-custom");
                if (customInput) {
                    customInput.style.display = this.value === "custom" ? "block" : "none";
                }
            });
        }

        if (playbackSelect) {
            playbackSelect.addEventListener("change", function () {
                var customInput = document.getElementById("audio-playback-custom");
                if (customInput) {
                    customInput.style.display = this.value === "custom" ? "block" : "none";
                }
            });
        }
    },

    saveConfig: function () {
        var captureDevice = document.getElementById("audio-capture").value;
        if (captureDevice === "custom") {
            captureDevice = document.getElementById("audio-capture-custom").value;
        }

        var playbackDevice = document.getElementById("audio-playback").value;
        if (playbackDevice === "custom") {
            playbackDevice = document.getElementById("audio-playback-custom").value;
        }

        var config = {
            video: {
                game_mode: parseInt(document.getElementById("hdmi-game-mode").value),
                vrr_mode: parseInt(document.getElementById("hdmi-vrr-mode").value),
                hdmi_source: document.getElementById("hdmi-source").value
            },
            audio: {
                enabled: document.getElementById("audio-enabled").checked,
                capture_device: captureDevice,
                playback_device: playbackDevice,
                latency_us: parseInt(document.getElementById("audio-latency").value),
                sample_format: "S16_LE",
                channels: parseInt(document.getElementById("audio-channels").value),
                sample_rate: parseInt(document.getElementById("audio-sample-rate").value)
            },
            hdcp: {
                enabled: false,
                version: "auto"
            },
            debug: {
                trace_level: 0
            }
        };

        var saveBtn = document.getElementById("save-hdmi-config");
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";

        callDBus("SetHdmiConfig", [JSON.stringify(config)])
            .done(function (success) {
                saveBtn.disabled = false;
                saveBtn.textContent = "Save & Apply";

                if (success) {
                    showNotification("success", "HDMI settings saved and applied");
                    HdmiSettings.loadConfig();
                } else {
                    showNotification("error", "Failed to save HDMI settings");
                }
            })
            .fail(function (error) {
                saveBtn.disabled = false;
                saveBtn.textContent = "Save & Apply";
                console.error("Failed to save HDMI config:", error);
                showNotification("error", "Failed to save: " + error.message);
            });
    }
};
