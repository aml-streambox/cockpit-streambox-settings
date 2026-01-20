/**
 * Network Settings Module
 * Handles wired network, WiFi client, and WiFi AP configuration
 */

const NetworkSettings = {
    currentStatus: {},
    wiredConfig: {},
    wifiNetworks: [],
    apConfig: {},

    init: function () {
        console.log("Initializing Network Settings");
        this.loadNetworkStatus();
        this.loadWiredConfig();
        this.loadWifiApConfig();
        this.setupEventListeners();
        this.setupCollapsiblePanels();
    },

    setupCollapsiblePanels: function () {
        document.querySelectorAll(".sbs-collapsible-header").forEach(function (header) {
            header.addEventListener("click", function () {
                var panel = this.closest(".sbs-collapsible");
                if (panel) {
                    panel.classList.toggle("sbs-collapsed");
                }
            });
        });
    },

    loadNetworkStatus: function () {
        callDBus("GetNetworkStatus")
            .done(function (result) {
                var status = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(status)) {
                    status = typeof status[0] === 'string' ? JSON.parse(status[0]) : status[0];
                }
                NetworkSettings.currentStatus = status;
                NetworkSettings.displayNetworkStatus(status);
                console.log("Network status loaded:", status);
            })
            .fail(function (error) {
                console.error("Failed to load network status:", error);
                showNotification("error", "Failed to load network status");
            });
    },

    displayNetworkStatus: function (status) {
        var statusContainer = document.getElementById("network-status");
        if (!statusContainer) return;

        var html = "";
        var interfaces = status.interfaces || [];

        interfaces.forEach(function (iface) {
            var stateClass = iface.state === "up" ? "sbs-status-up" : "sbs-status-down";
            var stateText = iface.state === "up" ? "Connected" : "Disconnected";

            html += '<div class="sbs-interface-item">';
            html += '  <div class="sbs-interface-info">';
            html += '    <span class="sbs-interface-name">' + iface.name + '</span>';
            html += '    <span class="sbs-interface-type">(' + iface.type + ')</span>';
            html += '  </div>';
            html += '  <div class="sbs-interface-status">';
            html += '    <span class="sbs-status-dot ' + stateClass + '"></span>';
            html += '    <span>' + stateText + '</span>';
            html += '  </div>';
            if (iface.ip_address) {
                html += '  <div class="sbs-interface-ip">' + iface.ip_address + '</div>';
            }
            html += '</div>';
        });

        statusContainer.innerHTML = html || '<p>No network interfaces found</p>';
    },

    loadWiredConfig: function () {
        callDBus("GetWiredConfig", ["eth0"])
            .done(function (result) {
                var config = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(config)) {
                    config = typeof config[0] === 'string' ? JSON.parse(config[0]) : config[0];
                }
                NetworkSettings.wiredConfig = config;
                NetworkSettings.populateWiredForm(config);
                console.log("Wired config loaded:", config);
            })
            .fail(function (error) {
                console.error("Failed to load wired config:", error);
            });
    },

    populateWiredForm: function (config) {
        var methodSelect = document.getElementById("wired-method");
        var ipInput = document.getElementById("wired-ip");
        var netmaskInput = document.getElementById("wired-netmask");
        var gatewayInput = document.getElementById("wired-gateway");
        var dnsInput = document.getElementById("wired-dns");

        if (methodSelect) methodSelect.value = config.method || "dhcp";
        if (ipInput) ipInput.value = config.ip_address || "";
        if (netmaskInput) netmaskInput.value = config.netmask || "255.255.255.0";
        if (gatewayInput) gatewayInput.value = config.gateway || "";
        if (dnsInput) dnsInput.value = (config.dns_servers || []).join(", ");

        this.toggleStaticIpFields("wired", config.method === "static");
    },

    toggleStaticIpFields: function (prefix, show) {
        var staticFields = document.getElementById(prefix + "-static-fields");
        if (staticFields) {
            staticFields.style.display = show ? "block" : "none";
        }
    },

    setupEventListeners: function () {
        var self = this;

        // Wired method change
        var wiredMethodSelect = document.getElementById("wired-method");
        if (wiredMethodSelect) {
            wiredMethodSelect.addEventListener("change", function () {
                self.toggleStaticIpFields("wired", this.value === "static");
            });
        }

        // WiFi method change
        var wifiMethodSelect = document.getElementById("wifi-method");
        if (wifiMethodSelect) {
            wifiMethodSelect.addEventListener("change", function () {
                self.toggleStaticIpFields("wifi", this.value === "static");
            });
        }

        // Save wired config
        var saveWiredBtn = document.getElementById("save-wired-config");
        if (saveWiredBtn) {
            saveWiredBtn.addEventListener("click", function () {
                self.saveWiredConfig();
            });
        }

        // Scan WiFi
        var scanWifiBtn = document.getElementById("scan-wifi");
        if (scanWifiBtn) {
            scanWifiBtn.addEventListener("click", function () {
                self.scanWifiNetworks();
            });
        }

        // Connect WiFi
        var connectWifiBtn = document.getElementById("connect-wifi");
        if (connectWifiBtn) {
            connectWifiBtn.addEventListener("click", function () {
                self.connectToWifi();
            });
        }

        // Toggle AP
        var apEnableToggle = document.getElementById("ap-enabled");
        if (apEnableToggle) {
            apEnableToggle.addEventListener("change", function () {
                self.toggleApFields(this.checked);
            });
        }

        // Save AP config
        var saveApBtn = document.getElementById("save-ap-config");
        if (saveApBtn) {
            saveApBtn.addEventListener("click", function () {
                self.saveApConfig();
            });
        }

        // Clear manual SSID when selecting from dropdown
        var ssidSelect = document.getElementById("wifi-ssid");
        if (ssidSelect) {
            ssidSelect.addEventListener("change", function () {
                if (this.value) {
                    var manualInput = document.getElementById("wifi-ssid-manual");
                    if (manualInput) manualInput.value = "";
                }
            });
        }
    },

    saveWiredConfig: function () {
        var method = document.getElementById("wired-method").value;
        var config = {
            interface: "eth0",
            method: method
        };

        if (method === "static") {
            config.ip_address = document.getElementById("wired-ip").value;
            config.netmask = document.getElementById("wired-netmask").value;
            config.gateway = document.getElementById("wired-gateway").value;
            var dnsStr = document.getElementById("wired-dns").value;
            config.dns_servers = dnsStr ? dnsStr.split(",").map(function (s) { return s.trim(); }) : [];
        }

        var saveBtn = document.getElementById("save-wired-config");
        saveBtn.disabled = true;

        callDBus("SetWiredConfig", [JSON.stringify(config)])
            .done(function (success) {
                saveBtn.disabled = false;
                if (success) {
                    showNotification("success", "Network configuration saved");
                    NetworkSettings.loadNetworkStatus();
                } else {
                    showNotification("error", "Failed to save network configuration");
                }
            })
            .fail(function (error) {
                saveBtn.disabled = false;
                console.error("Failed to save wired config:", error);
                showNotification("error", "Failed to save: " + error.message);
            });
    },

    scanWifiNetworks: function () {
        var scanBtn = document.getElementById("scan-wifi");
        var networkList = document.getElementById("wifi-networks");

        scanBtn.disabled = true;
        scanBtn.textContent = "Scanning...";
        networkList.innerHTML = '<p class="sbs-loading">Scanning for networks...</p>';

        callDBus("ScanWifiNetworks", ["wlan0"])
            .done(function (result) {
                scanBtn.disabled = false;
                scanBtn.textContent = "Scan";

                var networks = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(networks) && typeof networks[0] === 'string') {
                    networks = JSON.parse(networks[0]);
                }

                NetworkSettings.wifiNetworks = networks;
                NetworkSettings.displayWifiNetworks(networks);
            })
            .fail(function (error) {
                scanBtn.disabled = false;
                scanBtn.textContent = "Scan";
                console.error("Failed to scan WiFi networks:", error);
                networkList.innerHTML = '<p class="sbs-error">Failed to scan networks</p>';
            });
    },

    displayWifiNetworks: function (networks) {
        var networkList = document.getElementById("wifi-networks");
        var ssidSelect = document.getElementById("wifi-ssid");

        if (!networks || networks.length === 0) {
            networkList.innerHTML = '<p>No networks found</p>';
            return;
        }

        var html = "";
        networks.forEach(function (net) {
            var signalClass = net.signal > -50 ? "sbs-signal-strong" :
                net.signal > -70 ? "sbs-signal-medium" : "sbs-signal-weak";
            var securityIcon = net.security !== "open" ? "🔒" : "";

            html += '<div class="sbs-wifi-item" data-ssid="' + net.ssid + '">';
            html += '  <span class="sbs-wifi-ssid">' + net.ssid + '</span>';
            html += '  <span class="sbs-wifi-security">' + securityIcon + '</span>';
            html += '  <span class="sbs-wifi-signal ' + signalClass + '">' + net.signal + ' dBm</span>';
            html += '</div>';
        });
        networkList.innerHTML = html;

        if (ssidSelect) {
            ssidSelect.innerHTML = '<option value="">Select network...</option>';
            networks.forEach(function (net) {
                var option = document.createElement("option");
                option.value = net.ssid;
                option.textContent = net.ssid;
                ssidSelect.appendChild(option);
            });
        }

        document.querySelectorAll(".sbs-wifi-item").forEach(function (item) {
            item.addEventListener("click", function () {
                var ssid = this.getAttribute("data-ssid");
                if (ssidSelect && ssid) {
                    ssidSelect.value = ssid;
                    var manualInput = document.getElementById("wifi-ssid-manual");
                    if (manualInput) manualInput.value = "";
                }
            });
        });
    },

    connectToWifi: function () {
        var ssidSelect = document.getElementById("wifi-ssid");
        var ssidManual = document.getElementById("wifi-ssid-manual");
        var ssid = (ssidManual && ssidManual.value.trim()) ? ssidManual.value.trim() : ssidSelect.value;
        var password = document.getElementById("wifi-password").value;
        var method = document.getElementById("wifi-method").value;

        if (!ssid) {
            showNotification("error", "Please select or enter a network");
            return;
        }

        var config = {
            interface: "wlan0",
            ssid: ssid,
            password: password,
            method: method
        };

        if (method === "static") {
            config.ip_config = {
                ip_address: document.getElementById("wifi-ip").value,
                netmask: document.getElementById("wifi-netmask").value,
                gateway: document.getElementById("wifi-gateway").value
            };
        }

        var connectBtn = document.getElementById("connect-wifi");
        connectBtn.disabled = true;
        connectBtn.textContent = "Connecting...";

        callDBus("ConnectWifi", [JSON.stringify(config)])
            .done(function (success) {
                connectBtn.disabled = false;
                connectBtn.textContent = "Connect";

                if (success) {
                    showNotification("success", "Connected to " + ssid);
                    NetworkSettings.loadNetworkStatus();
                } else {
                    showNotification("error", "Failed to connect to " + ssid);
                }
            })
            .fail(function (error) {
                connectBtn.disabled = false;
                connectBtn.textContent = "Connect";
                console.error("Failed to connect WiFi:", error);
                showNotification("error", "Connection failed: " + error.message);
            });
    },

    loadWifiApConfig: function () {
        callDBus("GetWifiApConfig")
            .done(function (result) {
                var config = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(config)) {
                    config = typeof config[0] === 'string' ? JSON.parse(config[0]) : config[0];
                }
                NetworkSettings.apConfig = config;
                NetworkSettings.populateApForm(config);
                console.log("AP config loaded:", config);
            })
            .fail(function (error) {
                console.error("Failed to load AP config:", error);
            });
    },

    populateApForm: function (config) {
        var enabledToggle = document.getElementById("ap-enabled");
        var ssidInput = document.getElementById("ap-ssid");
        var passwordInput = document.getElementById("ap-password");
        var channelInput = document.getElementById("ap-channel");
        var ipInput = document.getElementById("ap-ip");

        if (enabledToggle) enabledToggle.checked = config.enabled || false;
        if (ssidInput) ssidInput.value = config.ssid || "StreamBox-AP";
        if (passwordInput) passwordInput.value = config.password || "";
        if (channelInput) channelInput.value = config.channel || 6;
        if (ipInput) ipInput.value = config.ip_address || "192.168.4.1";

        this.toggleApFields(config.enabled);
    },

    toggleApFields: function (show) {
        var apFields = document.getElementById("ap-config-fields");
        if (apFields) {
            apFields.style.display = show ? "block" : "none";
        }
    },

    saveApConfig: function () {
        var config = {
            enabled: document.getElementById("ap-enabled").checked,
            ssid: document.getElementById("ap-ssid").value,
            password: document.getElementById("ap-password").value,
            channel: parseInt(document.getElementById("ap-channel").value) || 6,
            interface: "wlan0",
            ip_address: document.getElementById("ap-ip").value || "192.168.4.1"
        };

        if (config.enabled && config.password.length < 8) {
            showNotification("error", "AP password must be at least 8 characters");
            return;
        }

        var saveBtn = document.getElementById("save-ap-config");
        saveBtn.disabled = true;

        callDBus("SetWifiApConfig", [JSON.stringify(config)])
            .done(function (success) {
                saveBtn.disabled = false;
                if (success) {
                    showNotification("success", "Access Point configuration saved");
                    NetworkSettings.loadNetworkStatus();
                } else {
                    showNotification("error", "Failed to save AP configuration");
                }
            })
            .fail(function (error) {
                saveBtn.disabled = false;
                console.error("Failed to save AP config:", error);
                showNotification("error", "Failed to save: " + error.message);
            });
    },

    refresh: function () {
        this.loadNetworkStatus();
        this.loadWiredConfig();
        this.loadWifiApConfig();
    }
};
