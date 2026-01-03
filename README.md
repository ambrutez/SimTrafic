# Simulación de Tráfico en Python 🚗💨

Este proyecto es una simulación de tráfico visual desarrollada en Python con **Pygame**. Modela el comportamiento vehicular en un circuito ovalado, permitiendo experimentar con congestiones, cuellos de botella y "ondas de choque" de tráfico.

## Características

*   **Circuito Ovalado Multicarril**: Los vehículos circulan por una pista con rectas y curvas.
*   **Comportamiento Inteligente**: Usa el *Intelligent Driver Model* (IDM) para aceleración y frenado, y modelos de cambio de carril (MOBIL simplificado).
*   **Zonas de Velocidad Dinámicas**: Configura tramos del circuito con límites de velocidad variables en tiempo real.
*   **Visualización de Congestión**: Código de colores para identificar rápidamente zonas de tráfico lento (Naranja) o detenido (Rojo).
*   **Controles en Tiempo Real**: Ajusta la cantidad de coches y los límites de velocidad (km/h) mientras la simulación corre.

## Requisitos

*   Python 3.x
*   Pygame

## Instalación

1.  Clona el repositorio o descarga el código.
2.  Instala las dependencias:
    ```bash
    pip install pygame
    ```

## Uso

Ejecuta el script principal:

```bash
python main.py
```

Usa los controles deslizantes en la pantalla para modificar la simulación.

## Estructura del Proyecto

*   `main.py`: Punto de entrada, manejo de ventana Pygame y UI.
*   `model.py`: Lógica física de los vehículos (aceleración, colisiones, cambio de carril).
*   `simulation.py`: Controlador de la simulación, gestión de la lista de vehículos y generación.

## Autor

Desarrollado como una prueba de concepto tecnológica para simulación de sistemas dinámicos.
