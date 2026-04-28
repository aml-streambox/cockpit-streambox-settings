const ApplicationSettings = {
    status: {},
    switching: false,

    init: function () {
        console.log("Initializing Application Settings");
        this.setupEventListeners();
        this.loadStatus();
    },

    parseResult: function (result) {
        var status = typeof result === "string" ? JSON.parse(result) : result;
        if (Array.isArray(status)) {
            status = typeof status[0] === "string" ? JSON.parse(status[0]) : status[0];
        }
        return status;
    },

    setupEventListeners: function () {
        var self = this;
        var applyBtn = document.getElementById("apply-application");
        var select = document.getElementById("active-application");

        if (applyBtn) {
            applyBtn.addEventListener("click", function () {
                self.switchApplication();
            });
        }

        if (select) {
            select.addEventListener("change", function () {
                self.updateApplyButton();
            });
        }
    },

    loadStatus: function () {
        callDBus("GetApplicationStatus")
            .done(function (result) {
                ApplicationSettings.status = ApplicationSettings.parseResult(result);
                ApplicationSettings.populateForm(ApplicationSettings.status);
                console.log("Application status loaded:", ApplicationSettings.status);
            })
            .fail(function (error) {
                console.error("Failed to load application status:", error);
                showNotification("error", "Failed to load application status");
            });
    },

    populateForm: function (status) {
        var select = document.getElementById("active-application");
        var statusText = document.getElementById("application-status");

        if (!select) return;

        select.innerHTML = "";
        (status.applications || []).forEach(function (app) {
            var option = document.createElement("option");
            option.value = app.id;
            option.disabled = !app.available;
            option.textContent = app.name + (app.available ? "" : " (not installed)");
            select.appendChild(option);
        });

        select.value = status.active_application || status.default_application || "gst-manager";
        select.disabled = this.switching;

        if (statusText) {
            statusText.classList.toggle("sbs-error", !!status.conflict);
            statusText.textContent = this.getStatusText(status);
        }

        this.updateApplyButton();
    },

    getStatusText: function (status) {
        var applications = status.applications || [];
        var activeApps = applications.filter(function (app) { return app.active; });
        var selectedApp = applications.find(function (app) {
            return app.id === status.active_application;
        });

        if (status.conflict) {
            return "Both services are running. Apply a selection to stop the other service.";
        }

        if (activeApps.length === 1) {
            return activeApps[0].name + " is currently running.";
        }

        if (selectedApp && selectedApp.enabled) {
            return selectedApp.name + " is enabled but not currently running.";
        }

        return "No Streambox application service is currently running.";
    },

    getSelectedApplication: function () {
        var select = document.getElementById("active-application");
        if (!select) return null;
        return select.value;
    },

    getApplicationById: function (applicationId) {
        var applications = this.status.applications || [];
        return applications.find(function (app) { return app.id === applicationId; });
    },

    updateApplyButton: function () {
        var applyBtn = document.getElementById("apply-application");
        var selectedApp = this.getApplicationById(this.getSelectedApplication());
        if (!applyBtn) return;

        applyBtn.disabled = this.switching || !selectedApp || !selectedApp.available;
    },

    switchApplication: function () {
        var self = this;
        var applicationId = this.getSelectedApplication();
        var selectedApp = this.getApplicationById(applicationId);

        if (!selectedApp || !selectedApp.available) {
            showNotification("error", "Selected application is not available");
            return;
        }

        if (!confirm("Switching applications will stop the current service and start " + selectedApp.name + ". Continue?")) {
            return;
        }

        var applyBtn = document.getElementById("apply-application");
        var select = document.getElementById("active-application");

        self.switching = true;
        if (applyBtn) {
            applyBtn.disabled = true;
            applyBtn.textContent = "Switching...";
        }
        if (select) select.disabled = true;

        callDBus("SetActiveApplication", [applicationId])
            .done(function (success) {
                var switched = Array.isArray(success) ? success[0] : success;
                self.switching = false;
                if (applyBtn) applyBtn.textContent = "Switch Application";
                if (select) select.disabled = false;

                if (switched) {
                    showNotification("success", "Application switched to " + selectedApp.name);
                } else {
                    showNotification("error", "Failed to switch application");
                }
                self.loadStatus();
            })
            .fail(function (error) {
                self.switching = false;
                if (applyBtn) applyBtn.textContent = "Switch Application";
                if (select) select.disabled = false;
                console.error("Failed to switch application:", error);
                showNotification("error", "Failed to switch application: " + error.message);
                self.loadStatus();
            });
    },

    refresh: function () {
        this.loadStatus();
    }
};
