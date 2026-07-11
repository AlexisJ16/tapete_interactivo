# Tapete Interactivo — Guia rapida

## Para empezar (una sola vez)

1. Conecta el tapete al computador con el cable USB.
2. Espera unos segundos. Windows 11 suele reconocerlo solo.
   - Si mas adelante el programa avisa que no encuentra el tapete, abre la carpeta
     `driver_cp210x`, descomprime el archivo y ejecuta el instalador que trae.
     Luego desconecta y vuelve a conectar el tapete.

## Uso diario

1. Conecta el tapete por USB (si no lo esta).
2. Doble clic en **TapeteDashboard.exe**.
3. El programa busca el tapete y se conecta solo. No tienes que elegir puertos.
4. **Elige al niño** en la lista de arriba. Si es la primera vez que viene, pulsa
   **Nuevo niño…**, escribe su nombre y un identificador (por ejemplo, el numero de
   su historia clinica).

   > Elige siempre al niño de la lista, no crees uno nuevo cada sesion: asi todas sus
   > terapias quedan juntas y puedes ver su evolucion.

5. Elige el **modo** de juego y el **nivel**, y presiona **Iniciar**.

## Ver las terapias anteriores de un niño

Abre la pestaña **Historico**:

- Arriba eliges al **niño**.
- Debajo aparece la **tabla con todas sus terapias**: fecha, modo, nivel, aciertos,
  errores y porcentaje de acierto.
- Mas abajo, la **grafica de su evolucion** a lo largo de las sesiones.

## Guardar el reporte de una terapia (CSV o PDF)

- **De la sesion que acabas de hacer:** en la pantalla **En vivo**, boton
  **Exportar CSV** o **Exportar PDF**.
- **De una terapia anterior:** en la pestaña **Historico**, elige al niño, haz clic en
  la fila de la terapia que quieras y pulsa **Exportar la terapia elegida**.

En los dos casos el programa te **pregunta donde guardar el archivo** (te propone la
carpeta Documentos y un nombre con el niño y la fecha). El PDF trae el resumen de la
sesion y una grafica; el CSV sirve para abrirlo en Excel.

## Si el tapete no esta conectado

El programa abre igual en **modo practica**: puedes tocar los botones con el raton
para conocer la interfaz. Para jugar de verdad, conecta el tapete y vuelve a abrir.

## Problemas frecuentes

- **"No se detecto el tapete"**: revisa el cable USB y que este bien conectado. Si
  sigue, instala el driver de la carpeta `driver_cp210x` (ver arriba).
- **El programa no abre**: descomprime el ZIP completo en una carpeta antes de
  ejecutar (no lo abras desde dentro del ZIP).
- **El boton de exportar dice que no hay sesion**: primero juega una terapia, o entra
  en **Historico** y elige una de la tabla.
