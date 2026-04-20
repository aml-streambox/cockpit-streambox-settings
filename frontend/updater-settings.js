var UpdaterSettings = {
    CHUNK_SIZE: 4 * 1024 * 1024,
    UPLOAD_PATH: "/data/software.swu.upload",
    _statusInterval: null,
    _file: null,
    _uploading: false,
    _proc: null,

    init: function () {
        console.log("Initializing Updater Settings");
        this.setupEventListeners();
        this.loadStatus();
    },

    setupEventListeners: function () {
        var self = this;

        var dropZone = document.getElementById("updater-drop-zone");
        var fileInput = document.getElementById("updater-file-input");
        var startBtn = document.getElementById("updater-start-btn");
        var cancelBtn = document.getElementById("updater-cancel-btn");
        var refreshBtn = document.getElementById("updater-refresh-btn");

        if (dropZone) {
            dropZone.addEventListener("click", function () {
                if (!self._uploading && fileInput) fileInput.click();
            });
            dropZone.addEventListener("dragover", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add("sbs-updater-dragover");
            });
            dropZone.addEventListener("dragleave", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove("sbs-updater-dragover");
            });
            dropZone.addEventListener("drop", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove("sbs-updater-dragover");
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    self.handleFile(e.dataTransfer.files[0]);
                }
            });
        }

        if (fileInput) {
            fileInput.addEventListener("change", function () {
                if (this.files && this.files.length > 0) {
                    self.handleFile(this.files[0]);
                }
            });
        }

        if (startBtn) {
            startBtn.addEventListener("click", function () {
                self.triggerUpdate();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener("click", function () {
                self.cancelUpload();
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener("click", function () {
                self.loadStatus();
            });
        }
    },

    handleFile: function (file) {
        if (!file || !file.name.endsWith(".swu")) {
            showNotification("error", "Please select a .swu update package");
            return;
        }

        this._file = file;

        var fileInfo = document.getElementById("updater-file-info");
        if (fileInfo) {
            fileInfo.textContent = file.name + " (" + UpdaterSettings.formatSize(file.size) + ")";
            fileInfo.style.display = "block";
        }

        this.uploadFile(file);
    },

    uploadFile: function (file) {
        var self = this;
        if (self._uploading) return;
        self._uploading = true;
        self.setUIState("uploading");

        var proc = cockpit.script(
            "cat > " + self.UPLOAD_PATH,
            [],
            { binary: true, superuser: "try", err: "message" }
        );
        self._proc = proc;

        var offset = 0;
        var reading = false;

        function sendNextChunk() {
            if (offset >= file.size) {
                proc.input(new Uint8Array(0), false);
                return;
            }
            if (reading) return;
            reading = true;

            var end = Math.min(offset + self.CHUNK_SIZE, file.size);
            var slice = file.slice(offset, end);
            var reader = new FileReader();

            reader.onload = function (e) {
                reading = false;
                offset = end;
                self.updateProgressBar((offset / file.size) * 100);
                proc.input(new Uint8Array(e.target.result), true);
                sendNextChunk();
            };

            reader.onerror = function () {
                proc.close("internal-error");
            };

            reader.readAsArrayBuffer(slice);
        }

        sendNextChunk();

        proc.then(function () {
            self._proc = null;
            self._verifyUploaded();
        }).fail(function (error) {
            self._proc = null;
            self._uploading = false;
            showNotification("error", "Upload failed: " + (error.message || error));
            self.loadStatus();
        });
    },

    _verifyUploaded: function () {
        var self = this;
        self.setUIState("verifying");

        callDBus("ImportLocalFile", [self.UPLOAD_PATH, ""])
            .done(function (result) {
                self._uploading = false;
                if (result) {
                    showNotification("success", "Upload verified. Ready to update.");
                    self.loadStatus();
                } else {
                    showNotification("error", "Verification failed.");
                    self.loadStatus();
                }
            })
            .fail(function (error) {
                self._uploading = false;
                showNotification("error", "Verification failed: " + error.message);
                self.loadStatus();
            });
    },

    triggerUpdate: function () {
        if (!confirm("This will reboot the device to apply the update. Any active streaming will be interrupted. Continue?")) {
            return;
        }

        var self = this;

        callDBus("TriggerUpdate")
            .done(function (result) {
                if (result) {
                    self.setUIState("updating");
                    showNotification("success", "Update triggered. Device will reboot shortly...");
                    self._startStatusPolling();
                } else {
                    showNotification("error", "Failed to trigger update");
                }
            })
            .fail(function (error) {
                showNotification("error", "Trigger failed: " + error.message);
            });
    },

    cancelUpload: function () {
        var self = this;

        if (self._proc) {
            self._proc.close("cancelled");
            self._proc = null;
        }

        callDBus("CancelUpload")
            .done(function () {
                self._uploading = false;
                self._file = null;
                showNotification("success", "Upload cancelled");
                self.loadStatus();
            })
            .fail(function (error) {
                self._uploading = false;
                showNotification("error", "Cancel failed: " + error.message);
                self.loadStatus();
            });
    },

    loadStatus: function () {
        var self = this;

        callDBus("GetUpdaterStatus")
            .done(function (result) {
                var status = typeof result === "string" ? JSON.parse(result) : result;
                if (Array.isArray(status)) {
                    status = typeof status[0] === "string" ? JSON.parse(status[0]) : status[0];
                }
                self.updateUI(status);
            })
            .fail(function (error) {
                console.error("Failed to load updater status:", error);
            });
    },

    updateUI: function (status) {
        var versionEl = document.getElementById("updater-current-version");
        if (versionEl) {
            versionEl.textContent = status.current_version || "unknown";
        }

        this.setUIState(status.state);
        this.updateProgressBar(status.progress || 0);

        var errorEl = document.getElementById("updater-error");
        if (errorEl) {
            if (status.error) {
                errorEl.textContent = status.error;
                errorEl.style.display = "block";
            } else {
                errorEl.style.display = "none";
            }
        }
    },

    setUIState: function (state) {
        var dropZone = document.getElementById("updater-drop-zone");
        var progressSection = document.getElementById("updater-progress-section");
        var verifySection = document.getElementById("updater-verify-section");
        var readySection = document.getElementById("updater-ready-section");
        var updatingSection = document.getElementById("updater-updating-section");
        var startBtn = document.getElementById("updater-start-btn");
        var cancelBtn = document.getElementById("updater-cancel-btn");

        if (dropZone) dropZone.style.display = "none";
        if (progressSection) progressSection.style.display = "none";
        if (verifySection) verifySection.style.display = "none";
        if (readySection) readySection.style.display = "none";
        if (updatingSection) updatingSection.style.display = "none";
        if (startBtn) startBtn.disabled = true;
        if (cancelBtn) cancelBtn.style.display = "none";

        switch (state) {
            case "idle":
                if (dropZone) dropZone.style.display = "block";
                break;
            case "uploading":
                if (progressSection) progressSection.style.display = "block";
                if (cancelBtn) cancelBtn.style.display = "inline-block";
                break;
            case "verifying":
                if (verifySection) verifySection.style.display = "block";
                break;
            case "ready":
                if (readySection) readySection.style.display = "block";
                if (startBtn) startBtn.disabled = false;
                if (cancelBtn) cancelBtn.style.display = "inline-block";
                break;
            case "updating":
                if (updatingSection) updatingSection.style.display = "block";
                break;
            case "error":
                if (dropZone) dropZone.style.display = "block";
                if (cancelBtn) cancelBtn.style.display = "inline-block";
                break;
        }
    },

    updateProgressBar: function (progress) {
        var bar = document.getElementById("updater-progress-bar");
        var text = document.getElementById("updater-progress-text");
        if (bar) bar.style.width = progress.toFixed(1) + "%";
        if (text) text.textContent = progress.toFixed(1) + "%";
    },

    _startStatusPolling: function () {
        var self = this;
        if (self._statusInterval) clearInterval(self._statusInterval);

        self._statusInterval = setInterval(function () {
            self.loadStatus();
        }, 5000);
    },

    formatSize: function (bytes) {
        if (!bytes || bytes === 0) return "0 B";
        var units = ["B", "KB", "MB", "GB"];
        var i = 0;
        var size = bytes;
        while (size >= 1024 && i < units.length - 1) {
            size /= 1024;
            i++;
        }
        return size.toFixed(1) + " " + units[i];
    }
};
