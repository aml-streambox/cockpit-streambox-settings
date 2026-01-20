SUMMARY = "Cockpit plugin for managing Streambox settings"
DESCRIPTION = "A Cockpit plugin for managing system settings on Amlogic A311D2 (T6/T7) Streambox"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c08e744e04123f653a917e2c5479f554"

SRC_URI = "file://backend \
           file://frontend \
           file://yocto/files/streambox-settings.service \
           file://yocto/files/org.cockpit.StreamboxSettings.conf"

S = "${WORKDIR}"

DEPENDS = "python3 cockpit"
RDEPENDS:${PN} = "python3 python3-core python3-dbus python3-glib cockpit \
                   python3-pygobject python3-asyncio hostnamectl timedatectl localectl"

inherit systemd

do_install() {
    install -d ${D}${libdir}/streambox-settings
    install -m 0755 ${S}/backend/*.py ${D}${libdir}/streambox-settings/
    
    install -d ${D}${datadir}/cockpit/streambox-settings
    install -m 0644 ${S}/frontend/*.html ${D}${datadir}/cockpit/streambox-settings/
    install -m 0644 ${S}/frontend/*.js ${D}${datadir}/cockpit/streambox-settings/
    install -m 0644 ${S}/frontend/*.css ${D}${datadir}/cockpit/streambox-settings/
    install -m 0644 ${S}/frontend/manifest.json ${D}${datadir}/cockpit/streambox-settings/
    
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${S}/yocto/files/streambox-settings.service ${D}${systemd_system_unitdir}/
    
    install -d ${D}${sysconfdir}/streambox-tv
    
    install -d ${D}${sysconfdir}/dbus-1/system.d
    install -m 0644 ${S}/yocto/files/org.cockpit.StreamboxSettings.conf ${D}${sysconfdir}/dbus-1/system.d/
}

FILES:${PN} += "${libdir}/streambox-settings/* \
                ${datadir}/cockpit/streambox-settings/*"

SYSTEMD_SERVICE:${PN} = "streambox-settings.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

python3 -m py_compile ${D}${libdir}/streambox-settings/*.py || true

pkg_postinst:${PN}() {
    if [ -z "$D" ]; then
        systemctl daemon-reload
        systemctl enable --now streambox-settings.service
    fi
}

pkg_prerm:${PN}() {
    if [ -z "$D" ]; then
        systemctl disable --now streambox-settings.service
    fi
}

INSANE_SKIP:${PN} += "file-rdeps"
