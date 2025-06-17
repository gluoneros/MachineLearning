import numpy as np
from visualizacion import visualizar_datos

# Generar datos de ejemplo (reemplaza esto con tus datos reales)
np.random.seed(42)
X = np.random.rand(100) * 10  # Variable predictora
y = 2 * X + np.random.randn(100) * 2  # Variable objetivo con ruido

# Visualizar los datos
visualizar_datos(X, y) 