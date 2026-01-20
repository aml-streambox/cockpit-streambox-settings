const DBUS_SERVICE = "org.cockpit.StreamboxSettings";
const DBUS_OBJECT = "/org/cockpit/StreamboxSettings";
const DBUS_INTERFACE = "org.cockpit.StreamboxSettings";

let dbusProxy = null;
let basicSettingsInitialized = false;

function init() {
    setupTabs();
    setupNotification();
    connectDBus();
}

function connectDBus() {
    console.log("Attempting to connect to D-Bus service:", DBUS_SERVICE);

    dbusProxy = cockpit.dbus(DBUS_SERVICE, { bus: "system" });

    dbusProxy.wait(function () {
        console.log("Connected to Streambox Settings D-Bus service");

        if (!basicSettingsInitialized) {
            BasicSettings.init();
            if (typeof NetworkSettings !== 'undefined') {
                NetworkSettings.init();
            }
            if (typeof HdmiSettings !== 'undefined') {
                HdmiSettings.init();
            }
            if (typeof StorageSettings !== 'undefined') {
                StorageSettings.init();
            }
            basicSettingsInitialized = true;
        }

        setupDBusSignals();
    }).fail(function (error) {
        console.error("Failed to connect to D-Bus service:", error);
        console.error("Service name:", DBUS_SERVICE);
        console.error("Object path:", DBUS_OBJECT);
        console.error("Interface:", DBUS_INTERFACE);

        showNotification("error", "Failed to connect to Streambox Settings service: " + error.message);

        setTimeout(function () {
            connectDBus();
        }, 5000);
    });
}

function setupDBusSignals() {
    dbusProxy.addEventListener("signal", function (event, args) {
        const signalName = args[0];
        const signalData = args[1];

        switch (signalName) {
            case "BasicSettingsChanged":
                console.log("Basic settings changed:", signalData);
                BasicSettings.refresh();
                break;
            case "ConfigChanged":
                console.log("Config changed:", signalData);
                break;
            case "TvserverConfigChanged":
                console.log("TVServer config changed:", signalData);
                break;
        }
    });
}

function callDBus(method, args) {
    return dbusProxy.call(DBUS_OBJECT, DBUS_INTERFACE, method, args || []);
}

function setupTabs() {
    const tabs = document.querySelectorAll("#tabs .sbs-tabs-link");
    const tabContents = document.querySelectorAll(".tab-content");

    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            const targetTab = this.getAttribute("data-tab");

            tabs.forEach(function (t) {
                t.classList.remove("sbs-active");
            });
            this.classList.add("sbs-active");

            tabContents.forEach(function (content) {
                content.classList.remove("sbs-active");
            });

            const targetContent = document.getElementById(targetTab + "-tab");
            if (targetContent) {
                targetContent.classList.add("sbs-active");
            }
        });
    });
}

function setupNotification() {
    const closeBtn = document.getElementById("close-notification");
    if (closeBtn) {
        closeBtn.addEventListener("click", function () {
            hideNotification();
        });
    }
}

function showNotification(type, message) {
    const notification = document.getElementById("notification");
    const messageSpan = document.getElementById("notification-message");

    notification.classList.remove("sbs-hidden", "sbs-success", "sbs-error");
    notification.classList.add("sbs-" + type);

    messageSpan.textContent = message;

    setTimeout(function () {
        hideNotification();
    }, 5000);
}

function hideNotification() {
    const notification = document.getElementById("notification");
    notification.classList.add("sbs-hidden");
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add("sbs-error");
        element.setAttribute("data-error", message);
        showNotification("error", message);
    }
}

function clearError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove("sbs-error");
        element.removeAttribute("data-error");
    }
}

function validateHostname(hostname) {
    if (!hostname || hostname.length === 0) {
        return { valid: false, message: "Hostname cannot be empty" };
    }

    if (hostname.length > 253) {
        return { valid: false, message: "Hostname cannot exceed 253 characters" };
    }

    const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

    if (!hostnameRegex.test(hostname)) {
        return { valid: false, message: "Invalid hostname format" };
    }

    return { valid: true };
}

document.addEventListener("DOMContentLoaded", init);
