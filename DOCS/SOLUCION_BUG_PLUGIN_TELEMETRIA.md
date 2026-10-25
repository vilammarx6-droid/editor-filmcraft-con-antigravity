# Solución Definitiva: Bug de Comillas en Plugin de Telemetría (Windows)

> **Resumen Ejecutivo:**
> En sistemas Windows, el plugin `googlecloudtools.datacloud_telemetry` genera un conflicto crítico en el hook `PreToolUse` debido a un error de serialización en la ruta del archivo ejecutable. Esto inyecta comillas dobles escapadas anidadas (`\"C:\...\"`) que provocan fallos de sintaxis en Node.js (`SyntaxError`) y bloquean todas las llamadas a herramientas (`tool_calls`) del asistente de IA.
> Este documento detalla la causa raíz, la solución manual, la desactivación preventiva y el script automatizado provisto en este repositorio.

---

## 1. Síntomas del Problema

Cuando el bug está activo en Windows:
1. Cualquier llamada a una herramienta (`run_command`, `write_file`, etc.) falla de forma intermitente o persistente con errores del tipo:
   ```text
   Hook failure: jsonhook__googlecloudtools.datacloud_telemetry_PreToolUse_0_0
   SyntaxError: Unexpected token 'C', "C:\Users\m"... is not valid JSON
   ```
2. La consola solicita confirmación una y otra vez o cancela la ejecución sin reportar salida.
3. El agente queda en bucle intentando ejecutar herramientas que el hook previo intercepta y bloquea.

---

## 2. Causa Raíz Técnica

El archivo `hooks.json` o la configuración del plugin registrada en:
```text
C:\Users\<Usuario>\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\
```
registra el script ejecutable `telemetry_hook_bundle.js`. 

Al formatear rutas en Windows (especialmente cuando el nombre de usuario contiene espacios o caracteres especiales), el generador del plugin concatena comillas dobles adicionales:
```json
// Configuración defectuosa generada en Windows:
{
  "command": "\"C:\\Users\\<Usuario>\\.gemini\\config\\plugins\\googlecloudtools.datacloud_telemetry\\telemetry_hook_bundle.js\""
}
```
Al ser invocado por el ejecutor de subprocesos de Node.js / PowerShell, las comillas duplicadas escapan el argumento como una cadena JSON malformada o un comando inexistente, abortando el proceso antes de invocar la herramienta del agente.

---

## 3. Solución Automatizada (1 Clic)

Dentro de la carpeta `HERRAMIENTAS/` de este repositorio se han integrado scripts automáticos para reparar este fallo en cualquier momento:

### Opción A: Mediante PowerShell
Abre tu consola PowerShell y ejecuta:
```powershell
.\HERRAMIENTAS\reparar-plugin-telemetria.ps1
```

### Opción B: Mediante Python
```bash
python .\HERRAMIENTAS\reparar-plugin-telemetria.py
```

El script realiza de forma desatendida:
1. Inspección de `~/.gemini/config/plugins` en busca de archivos `hooks.json` con rutas escapadas o dañadas.
2. Limpieza de comillas anidadas en las rutas absolutas.
3. Eliminación segura de carpetas huérfanas de `googlecloudtools.datacloud_telemetry`.
4. Inyección de `"telemetry": { "enabled": false }` en `~/.gemini/config/config.json` y `settings.json` para blindar el entorno contra futuras actualizaciones conflictivas.

---

## 4. Solución Manual Paso a Paso

Si prefieres realizar la corrección manualmente:

### Paso 1: Corregir o Limpiar `hooks.json`
1. Dirígete a la carpeta raíz de plugins:
   ```text
   C:\Users\<Usuario>\.gemini\config\plugins\
   ```
2. Si existe la carpeta `googlecloudtools.datacloud_telemetry`, ábrela.
3. Si existe `hooks.json`, abre el archivo en Notepad o VS Code y asegúrate de que la ruta hacia `telemetry_hook_bundle.js` esté limpia, sin comillas adicionales dentro del string JSON:
   ```json
   "command": "C:\\Users\\<Usuario>\\.gemini\\config\\plugins\\googlecloudtools.datacloud_telemetry\\telemetry_hook_bundle.js"
   ```
   *(Si no utilizas métricas de Data Cloud, puedes eliminar directamente la carpeta `googlecloudtools.datacloud_telemetry`)*.

### Paso 2: Desactivar la Telemetría Globalmente
1. Abre tu archivo de configuración en:
   ```text
   C:\Users\<Usuario>\.gemini\config\config.json
   ```
   *(o `C:\Users\<Usuario>\.gemini\settings.json` según tu versión)*.
2. Agrega o actualiza el bloque de telemetría:
   ```json
   {
     "telemetry": {
       "enabled": false
     }
   }
   ```
3. Guarda el archivo y reinicia tu terminal o sesión de Antigravity / Gemini CLI.

---

## 5. Referencias y Discusión Oficial

* **Issue en GitHub:** [GoogleCloudPlatform/data-cloud-plugins - Windows hook path escaping issue](https://github.com/GoogleCloudPlatform/data-cloud-plugins/issues)
* **Foro de Desarrolladores de Google AI:** [Bug Windows: googlecloudtools.datacloud_telemetry pretooluse hook has malformed path blocking tool calls](https://discuss.ai.google.dev/)
