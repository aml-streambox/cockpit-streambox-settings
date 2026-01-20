/**
 * Storage Settings Module
 * Displays storage devices, mount points, and disk usage
 */

const StorageSettings = {
    storageInfo: {},

    init: function () {
        console.log("Initializing Storage Settings");
        this.setupEventListeners();
        this.loadStorageInfo();
    },

    setupEventListeners: function () {
        var self = this;
        var refreshBtn = document.getElementById("refresh-storage");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", function () {
                self.loadStorageInfo();
            });
        }
    },

    loadStorageInfo: function () {
        var loadingDiv = document.getElementById("storage-loading");
        var containerDiv = document.getElementById("storage-devices-container");
        var errorDiv = document.getElementById("storage-error");

        if (loadingDiv) loadingDiv.style.display = "block";
        if (containerDiv) containerDiv.style.display = "none";
        if (errorDiv) errorDiv.style.display = "none";

        callDBus("GetStorageInfo")
            .done(function (result) {
                var info = typeof result === 'string' ? JSON.parse(result) : result;
                if (Array.isArray(info)) {
                    info = typeof info[0] === 'string' ? JSON.parse(info[0]) : info[0];
                }
                StorageSettings.storageInfo = info;
                StorageSettings.displayStorageInfo(info);

                if (loadingDiv) loadingDiv.style.display = "none";
                if (containerDiv) containerDiv.style.display = "block";
                console.log("Storage info loaded:", info);
            })
            .fail(function (error) {
                console.error("Failed to load storage info:", error);
                if (loadingDiv) loadingDiv.style.display = "none";
                if (errorDiv) {
                    errorDiv.textContent = "Failed to load storage information: " + error.message;
                    errorDiv.style.display = "block";
                }
            });
    },

    displayStorageInfo: function (info) {
        var tbody = document.getElementById("storage-devices");
        var usbTbody = document.getElementById("usb-devices");
        var noUsbMsg = document.getElementById("no-usb-message");

        if (!tbody) return;

        tbody.innerHTML = "";
        if (usbTbody) usbTbody.innerHTML = "";

        var filesystems = info.filesystems || [];
        var usbDevices = [];

        filesystems.forEach(function (fs) {
            // Check if USB device
            var isUsb = fs.device && (fs.device.includes("/sd") || fs.device.includes("usb"));

            if (isUsb && usbTbody) {
                usbDevices.push(fs);
            }

            var row = document.createElement("tr");
            row.innerHTML =
                '<td>' + (fs.device || '-') + '</td>' +
                '<td>' + (fs.mount_point || '-') + '</td>' +
                '<td>' + (fs.fstype || '-') + '</td>' +
                '<td>' + StorageSettings.formatSize(fs.size) + '</td>' +
                '<td>' + StorageSettings.formatSize(fs.used) + '</td>' +
                '<td>' + StorageSettings.formatSize(fs.available) + '</td>' +
                '<td>' + StorageSettings.createUsageBar(fs.use_percent) + '</td>';
            tbody.appendChild(row);
        });

        // Display USB devices
        if (usbTbody) {
            if (usbDevices.length === 0) {
                if (noUsbMsg) noUsbMsg.style.display = "block";
                usbTbody.parentElement.style.display = "none";
            } else {
                if (noUsbMsg) noUsbMsg.style.display = "none";
                usbTbody.parentElement.style.display = "table";

                usbDevices.forEach(function (usb) {
                    var isMounted = usb.mount_point && usb.mount_point !== "";
                    var row = document.createElement("tr");
                    row.innerHTML =
                        '<td>' + (usb.device || '-') + '</td>' +
                        '<td>' + (usb.label || '-') + '</td>' +
                        '<td>' + (usb.mount_point || 'Not mounted') + '</td>' +
                        '<td class="' + (isMounted ? 'sbs-status-ok' : 'sbs-status-warn') + '">' +
                        (isMounted ? 'Mounted' : 'Unmounted') + '</td>' +
                        '<td>' +
                        '<button class="sbs-button sbs-button-small" ' +
                        'onclick="StorageSettings.' + (isMounted ? 'unmount' : 'mount') +
                        'Device(\'' + usb.device + '\')">' +
                        (isMounted ? 'Unmount' : 'Mount') +
                        '</button>' +
                        '</td>';
                    usbTbody.appendChild(row);
                });
            }
        }
    },

    formatSize: function (bytes) {
        if (!bytes || bytes === 0) return '-';

        var units = ['B', 'KB', 'MB', 'GB', 'TB'];
        var i = 0;
        var size = bytes;

        while (size >= 1024 && i < units.length - 1) {
            size /= 1024;
            i++;
        }

        return size.toFixed(1) + ' ' + units[i];
    },

    createUsageBar: function (percent) {
        if (percent === undefined || percent === null) return '-';

        var color = percent > 90 ? '#ff4444' : percent > 70 ? '#ffaa00' : '#44aa44';

        return '<div class="sbs-progress-bar">' +
            '<div class="sbs-progress-fill" style="width: ' + percent + '%; background-color: ' + color + ';"></div>' +
            '<span class="sbs-progress-text">' + percent + '%</span>' +
            '</div>';
    },

    mountDevice: function (device) {
        showNotification("info", "Mounting " + device + "...");

        callDBus("MountDevice", [device])
            .done(function (result) {
                if (result) {
                    showNotification("success", "Device mounted successfully");
                    StorageSettings.loadStorageInfo();
                } else {
                    showNotification("error", "Failed to mount device");
                }
            })
            .fail(function (error) {
                showNotification("error", "Mount failed: " + error.message);
            });
    },

    unmountDevice: function (device) {
        showNotification("info", "Unmounting " + device + "...");

        callDBus("UnmountDevice", [device])
            .done(function (result) {
                if (result) {
                    showNotification("success", "Device unmounted successfully");
                    StorageSettings.loadStorageInfo();
                } else {
                    showNotification("error", "Failed to unmount device");
                }
            })
            .fail(function (error) {
                showNotification("error", "Unmount failed: " + error.message);
            });
    }
};
