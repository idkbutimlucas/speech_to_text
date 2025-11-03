#!/bin/bash
# Script pour désactiver la veille sur Raspberry Pi

echo "🚫 Désactivation de la veille sur Raspberry Pi..."

# 1. Désactiver le screensaver et DPMS dans autostart
echo ""
echo "📝 Configuration de autostart..."
sudo bash -c 'cat >> /etc/xdg/lxsession/LXDE-pi/autostart << EOF
@xset s off
@xset -dpms
@xset s noblank
EOF'

# 2. Désactiver le blanking de la console
echo "📝 Désactivation du blanking console..."
if ! grep -q "consoleblank=0" /boot/cmdline.txt; then
    sudo sed -i 's/$/ consoleblank=0/' /boot/cmdline.txt
fi

# 3. Désactiver les services de suspension
echo "📝 Désactivation des services de suspension..."
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target 2>/dev/null

# 4. Configuration lightdm (si présent)
if [ -f /etc/lightdm/lightdm.conf ]; then
    echo "📝 Configuration de lightdm..."
    sudo bash -c 'grep -q "xserver-command=X -s 0 -dpms" /etc/lightdm/lightdm.conf || sed -i "/\[Seat:\*\]/a xserver-command=X -s 0 -dpms" /etc/lightdm/lightdm.conf'
fi

# 5. Désactiver xscreensaver s'il est installé
if command -v xscreensaver &> /dev/null; then
    echo "📝 Suppression de xscreensaver..."
    sudo apt remove xscreensaver -y -qq 2>/dev/null
fi

# 6. Configuration Wayland/GNOME (si présent)
if command -v gsettings &> /dev/null; then
    echo "📝 Configuration GNOME/Wayland..."
    gsettings set org.gnome.desktop.session idle-delay 0 2>/dev/null
    gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null
fi

echo ""
echo "✅ Configuration terminée!"
echo ""
echo "⚠️  IMPORTANT: Redémarrer le Raspberry Pi pour appliquer les changements:"
echo "   sudo reboot"
echo ""
