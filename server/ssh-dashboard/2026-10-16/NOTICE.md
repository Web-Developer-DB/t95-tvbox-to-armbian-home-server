# Herkunft und Umfang

Snapshot vom 16.10.2026 einer laufenden T95 mit Armbian-BSP `armbian-bsp-cli-tanix-tx6s-axp313-current` 26.8.4 und Kernel 6.18.48-current-sunxi64. Die Dateien wurden aus der Installation kopiert; Gleichheit mit einem unveränderten offiziellen Armbian-Release wird nicht behauptet. Es handelt sich um den im Projekt verwendeten, teilweise angepassten Stand.

Die MOTD-Bausteine und Allwinner-Hilfsfunktionen stammen aus dem Armbian-Umfeld. Ihre vorhandenen Copyright-/GPL-Hinweise wurden unverändert übernommen. Der Text der GPL Version 2 liegt zur Erhaltung dieser Hinweise in `COPYING.armbian.GPL-2`. Diese Datei legt keine neue Lizenz für das gesamte Repository fest; dessen bisheriger Lizenzstatus bleibt bestehen. Dateien ohne eigenen Lizenzheader werden durch diesen Hinweis nicht pauschal umlizenziert.

`95-sd-card-stats` ist die eigene Erweiterung der Installation. Sie ist nicht als Paketdatei des abgefragten BSP registriert. Ihre nicht ausführbare `+`-Sicherungskopie gehört nur zum privaten Ausgangsarchiv. `quotes.txt` ist der vorgefundene Hinweistext, kein auszuführendes Skript.

`manifest.json` enthält ausschließlich generische relative Dateiziele, Modi, Prüfsummen und die Softwarebasis. SSH-Schlüssel, Benutzerkonten, Zugangsdaten, originale IP-Adressen, persönliche Mountpfade, PAM-Authentifizierungskonfiguration und `/etc/armbian-release` sind nicht Bestandteil der installierbaren Nutzdaten.
