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
        var protocolSelect = document.getElementById("network-storage-protocol");
        var saveNetworkBtn = document.getElementById("save-network-storage");
        var saveMountNetworkBtn = document.getElementById("save-mount-network-storage");
        var cancelEditBtn = document.getElementById("cancel-network-storage-edit");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", function () {
                self.loadStorageInfo();
            });
        }
        if (protocolSelect) {
            protocolSelect.addEventListener("change", function () {
                self.updateNetworkStorageFields();
            });
        }
        if (saveNetworkBtn) {
            saveNetworkBtn.onclick = function () {
                self.saveNetworkStorageEntry(false);
            };
        }
        if (saveMountNetworkBtn) {
            saveMountNetworkBtn.onclick = function () {
                self.saveNetworkStorageEntry(true);
            };
        }
        if (cancelEditBtn) {
            cancelEditBtn.addEventListener("click", function () {
                self.clearNetworkStorageForm();
            });
        }
        this.updateNetworkStorageFields();
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

        this.displayNetworkStorageEntries(info.network_storage_entries || []);
    },

    displayNetworkStorageEntries: function (entries) {
        var tbody = document.getElementById("network-storage-mounts");
        var table = document.getElementById("network-storage-table");
        var emptyMsg = document.getElementById("no-network-storage-message");

        if (!tbody) return;

        tbody.innerHTML = "";
        if (entries.length === 0) {
            if (table) table.style.display = "none";
            if (emptyMsg) emptyMsg.style.display = "block";
            return;
        }

        if (table) table.style.display = "table";
        if (emptyMsg) emptyMsg.style.display = "none";

        entries.forEach(function (entry) {
            var row = document.createElement("tr");
            var nameCell = document.createElement("td");
            var remoteCell = document.createElement("td");
            var mountPointCell = document.createElement("td");
            var typeCell = document.createElement("td");
            var statusCell = document.createElement("td");
            var bootCell = document.createElement("td");
            var actionCell = document.createElement("td");

            nameCell.textContent = entry.name || "-";
            remoteCell.textContent = entry.remote || "-";
            mountPointCell.textContent = entry.mount_point || "-";
            typeCell.textContent = entry.fstype || "-";
            statusCell.textContent = entry.mounted ? "Mounted" : (entry.enabled ? "Ready" : "Disabled");
            statusCell.className = entry.mounted ? "sbs-status-ok" : (entry.enabled ? "" : "sbs-status-warn");
            if (entry.last_error) {
                statusCell.className = "sbs-error";
                statusCell.textContent = "Error: " + entry.last_error;
            }
            bootCell.textContent = entry.auto_mount ? "Auto" : "Manual";

            actionCell.appendChild(this.createNetworkActionButton(entry.mounted ? "Unmount" : "Mount", function () {
                if (entry.mounted) {
                    StorageSettings.unmountNetworkStorageEntry(entry.id);
                } else {
                    StorageSettings.mountNetworkStorageEntry(entry.id);
                }
            }, !entry.enabled && !entry.mounted));
            actionCell.appendChild(this.createNetworkActionButton(entry.enabled ? "Disable" : "Enable", function () {
                StorageSettings.setNetworkStorageEntryFlags(entry.id, !entry.enabled, entry.auto_mount);
            }, false));
            actionCell.appendChild(this.createNetworkActionButton(entry.auto_mount ? "Boot Off" : "Boot On", function () {
                StorageSettings.setNetworkStorageEntryFlags(entry.id, entry.enabled, !entry.auto_mount);
            }, false));
            actionCell.appendChild(this.createNetworkActionButton("Edit", function () {
                StorageSettings.populateNetworkStorageForm(entry);
            }, false));
            actionCell.appendChild(this.createNetworkActionButton("Delete", function () {
                StorageSettings.deleteNetworkStorageEntry(entry.id);
            }, false));

            row.appendChild(nameCell);
            row.appendChild(remoteCell);
            row.appendChild(mountPointCell);
            row.appendChild(typeCell);
            row.appendChild(statusCell);
            row.appendChild(bootCell);
            row.appendChild(actionCell);
            tbody.appendChild(row);
        }, this);
    },

    createNetworkActionButton: function (label, handler, disabled) {
        var button = document.createElement("button");
        button.className = "sbs-button sbs-button-small";
        button.textContent = label;
        button.disabled = !!disabled;
        button.style.marginRight = "6px";
        button.style.marginBottom = "6px";
        button.addEventListener("click", handler);
        return button;
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
    },

    parseActionResult: function (result) {
        var value = Array.isArray(result) ? result[0] : result;
        if (typeof value === "string") {
            try {
                return JSON.parse(value);
            } catch (e) {
                return { success: value === "true", error: value };
            }
        }
        if (typeof value === "boolean") {
            return { success: value };
        }
        return value || { success: false, error: "No response from settings service" };
    },

    setNetworkFeedback: function (type, message) {
        var feedback = document.getElementById("network-storage-feedback");
        if (!feedback) return;

        feedback.classList.remove("sbs-error", "sbs-status-ok");
        if (type === "error") feedback.classList.add("sbs-error");
        if (type === "success") feedback.classList.add("sbs-status-ok");
        feedback.textContent = message;
        feedback.style.display = message ? "block" : "none";
    },

    updateNetworkStorageFields: function () {
        var protocol = this.getInputValue("network-storage-protocol") || "nfs";
        var credentials = document.getElementById("network-storage-credentials");
        var remote = document.getElementById("network-storage-remote");
        var options = document.getElementById("network-storage-options");

        if (credentials) credentials.style.display = protocol === "smb" ? "block" : "none";
        if (remote) {
            remote.placeholder = protocol === "smb" ? "//server/share" : "server:/export/path";
        }
        if (options) {
            options.placeholder = protocol === "smb" ? "rw,vers=3.0" : "rw,vers=4";
        }
    },

    getInputValue: function (id) {
        var element = document.getElementById(id);
        return element ? element.value.trim() : "";
    },

    getInputChecked: function (id) {
        var element = document.getElementById(id);
        return element ? element.checked : false;
    },

    setInputValue: function (id, value) {
        var element = document.getElementById(id);
        if (element) element.value = value || "";
    },

    setInputChecked: function (id, value) {
        var element = document.getElementById(id);
        if (element) element.checked = !!value;
    },

    clearNetworkStorageForm: function () {
        this.setInputValue("network-storage-id", "");
        this.setInputValue("network-storage-name", "");
        this.setInputValue("network-storage-protocol", "nfs");
        this.setInputValue("network-storage-remote", "");
        this.setInputValue("network-storage-mount-point", "");
        this.setInputValue("network-storage-username", "");
        this.setInputValue("network-storage-password", "");
        this.setInputValue("network-storage-options", "");
        this.setInputChecked("network-storage-enabled", true);
        this.setInputChecked("network-storage-auto-mount", true);
        this.updateNetworkStorageFields();
        this.setNetworkFeedback("info", "");

        var saveBtn = document.getElementById("save-network-storage");
        var saveMountBtn = document.getElementById("save-mount-network-storage");
        var cancelBtn = document.getElementById("cancel-network-storage-edit");
        if (saveBtn) saveBtn.textContent = "Add Network Storage";
        if (saveMountBtn) saveMountBtn.textContent = "Add & Mount";
        if (cancelBtn) cancelBtn.style.display = "none";
    },

    populateNetworkStorageForm: function (entry) {
        this.setInputValue("network-storage-id", entry.id);
        this.setInputValue("network-storage-name", entry.name);
        this.setInputValue("network-storage-protocol", entry.protocol === "cifs" ? "smb" : entry.protocol);
        this.setInputValue("network-storage-remote", entry.remote);
        this.setInputValue("network-storage-mount-point", entry.mount_point);
        this.setInputValue("network-storage-username", entry.username);
        this.setInputValue("network-storage-password", "");
        this.setInputValue("network-storage-options", entry.options);
        this.setInputChecked("network-storage-enabled", entry.enabled);
        this.setInputChecked("network-storage-auto-mount", entry.auto_mount);
        this.updateNetworkStorageFields();
        this.setNetworkFeedback("info", "Editing " + (entry.name || entry.remote) + ". Leave password blank to keep the saved credential.");

        var saveBtn = document.getElementById("save-network-storage");
        var saveMountBtn = document.getElementById("save-mount-network-storage");
        var cancelBtn = document.getElementById("cancel-network-storage-edit");
        if (saveBtn) saveBtn.textContent = "Save Network Storage";
        if (saveMountBtn) saveMountBtn.textContent = "Save & Mount";
        if (cancelBtn) cancelBtn.style.display = "inline-block";
    },

    saveNetworkStorageEntry: function (mountAfterSave) {
        var entryId = this.getInputValue("network-storage-id");
        var name = this.getInputValue("network-storage-name");
        var protocol = this.getInputValue("network-storage-protocol") || "nfs";
        var remote = this.getInputValue("network-storage-remote");
        var mountPoint = this.getInputValue("network-storage-mount-point");
        var username = this.getInputValue("network-storage-username");
        var passwordElement = document.getElementById("network-storage-password");
        var password = passwordElement ? passwordElement.value : "";
        var options = this.getInputValue("network-storage-options");
        var enabled = this.getInputChecked("network-storage-enabled");
        var autoMount = this.getInputChecked("network-storage-auto-mount");

        if (!remote) {
            showNotification("error", "Remote path is required");
            return;
        }

        showNotification("info", "Saving network storage...");
        this.setNetworkFeedback("info", "Saving network storage...");

        callDBus("SaveNetworkStorageEntry", [entryId, name, protocol, remote, mountPoint, username, password, options, enabled, autoMount])
            .done(function (result) {
                var response = StorageSettings.parseActionResult(result);
                if (response.success) {
                    var savedEntry = response.entry || {};
                    StorageSettings.clearNetworkStorageForm();
                    if (response.warning) {
                        StorageSettings.setNetworkFeedback("error", "Saved, but cannot mount yet: " + response.warning);
                        showNotification("error", "Saved, but cannot mount yet: " + response.warning);
                    } else {
                        showNotification("success", "Network storage saved");
                        StorageSettings.setNetworkFeedback("success", "Network storage saved");
                    }
                    StorageSettings.loadStorageInfo();
                    if (mountAfterSave && savedEntry.id) {
                        StorageSettings.mountNetworkStorageEntry(savedEntry.id);
                    }
                } else {
                    var message = response.error || "Failed to save network storage";
                    StorageSettings.setNetworkFeedback("error", message);
                    showNotification("error", message);
                }
            })
            .fail(function (error) {
                var message = "Network storage save failed: " + error.message;
                StorageSettings.setNetworkFeedback("error", message);
                showNotification("error", message);
            });
    },

    mountNetworkStorageEntry: function (entryId) {
        showNotification("info", "Mounting network storage...");
        this.setNetworkFeedback("info", "Mounting network storage...");

        callDBus("MountNetworkStorageEntry", [entryId])
            .done(function (result) {
                var response = StorageSettings.parseActionResult(result);
                if (response.success) {
                    showNotification("success", "Network storage mounted successfully");
                    StorageSettings.setNetworkFeedback("success", "Mounted at " + response.mount_point);
                    StorageSettings.loadStorageInfo();
                } else {
                    var message = response.error || "Failed to mount network storage";
                    StorageSettings.setNetworkFeedback("error", message);
                    showNotification("error", message);
                }
            })
            .fail(function (error) {
                var message = "Network mount failed: " + error.message;
                StorageSettings.setNetworkFeedback("error", message);
                showNotification("error", message);
            });
    },

    unmountNetworkStorageEntry: function (entryId) {
        showNotification("info", "Unmounting network storage...");
        this.setNetworkFeedback("info", "Unmounting network storage...");

        callDBus("UnmountNetworkStorageEntry", [entryId])
            .done(function (result) {
                var response = StorageSettings.parseActionResult(result);
                if (response.success) {
                    showNotification("success", "Network storage unmounted successfully");
                    StorageSettings.setNetworkFeedback("success", "Network storage unmounted successfully");
                    StorageSettings.loadStorageInfo();
                } else {
                    var message = response.error || "Failed to unmount network storage";
                    StorageSettings.setNetworkFeedback("error", message);
                    showNotification("error", message);
                }
            })
            .fail(function (error) {
                var message = "Network unmount failed: " + error.message;
                StorageSettings.setNetworkFeedback("error", message);
                showNotification("error", message);
            });
    },

    setNetworkStorageEntryFlags: function (entryId, enabled, autoMount) {
        callDBus("SetNetworkStorageEntryFlags", [entryId, enabled, autoMount])
            .done(function (result) {
                var response = StorageSettings.parseActionResult(result);
                if (response.success) {
                    showNotification("success", "Network storage updated");
                    StorageSettings.loadStorageInfo();
                } else {
                    var message = response.error || "Failed to update network storage";
                    StorageSettings.setNetworkFeedback("error", message);
                    showNotification("error", message);
                }
            })
            .fail(function (error) {
                var message = "Network storage update failed: " + error.message;
                StorageSettings.setNetworkFeedback("error", message);
                showNotification("error", message);
            });
    },

    deleteNetworkStorageEntry: function (entryId) {
        if (!confirm("Delete this network storage entry? Mounted storage will be unmounted first.")) {
            return;
        }

        callDBus("DeleteNetworkStorageEntry", [entryId])
            .done(function (result) {
                var response = StorageSettings.parseActionResult(result);
                if (response.success) {
                    showNotification("success", "Network storage deleted");
                    StorageSettings.clearNetworkStorageForm();
                    StorageSettings.loadStorageInfo();
                } else {
                    var message = response.error || "Failed to delete network storage";
                    StorageSettings.setNetworkFeedback("error", message);
                    showNotification("error", message);
                }
            })
            .fail(function (error) {
                var message = "Network storage delete failed: " + error.message;
                StorageSettings.setNetworkFeedback("error", message);
                showNotification("error", message);
            });
    }
};
