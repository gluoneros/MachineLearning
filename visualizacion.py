import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def visualizar_datos(X, y):
    """
    Función para visualizar los datos y detectar valores atípicos
    
    Args:
        X: Variables predictoras
        y: Variable objetivo
    """
    # Crear figura con subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Gráfico de dispersión
    axes[0,0].scatter(X, y, alpha=0.5)
    axes[0,0].set_title('Gráfico de Dispersión')
    axes[0,0].set_xlabel('X')
    axes[0,0].set_ylabel('y')
    
    # 2. Boxplot de y
    axes[0,1].boxplot(y)
    axes[0,1].set_title('Boxplot de y')
    axes[0,1].set_ylabel('Valores')
    
    # 3. Histograma de y
    axes[1,0].hist(y, bins=30)
    axes[1,0].set_title('Histograma de y')
    axes[1,0].set_xlabel('Valores')
    axes[1,0].set_ylabel('Frecuencia')
    
    # 4. Gráfico de residuos
    from sklearn.linear_model import LinearRegression
    modelo = LinearRegression()
    modelo.fit(X.reshape(-1,1), y)
    y_pred = modelo.predict(X.reshape(-1,1))
    residuos = y - y_pred
    axes[1,1].scatter(y_pred, residuos, alpha=0.5)
    axes[1,1].axhline(y=0, color='r', linestyle='--')
    axes[1,1].set_title('Gráfico de Residuos')
    axes[1,1].set_xlabel('Valores Predichos')
    axes[1,1].set_ylabel('Residuos')
    
    plt.tight_layout()
    plt.show()
    
    # Calcular estadísticas descriptivas
    print("\nEstadísticas descriptivas de y:")
    print(f"Media: {np.mean(y):.2f}")
    print(f"Mediana: {np.median(y):.2f}")
    print(f"Desviación estándar: {np.std(y):.2f}")
    print(f"Valor mínimo: {np.min(y):.2f}")
    print(f"Valor máximo: {np.max(y):.2f}")
    
    # Detectar valores atípicos usando el método IQR
    Q1 = np.percentile(y, 25)
    Q3 = np.percentile(y, 75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR
    
    valores_atipicos = y[(y < limite_inferior) | (y > limite_superior)]
    print(f"\nNúmero de valores atípicos: {len(valores_atipicos)}")
    print(f"Límite inferior: {limite_inferior:.2f}")
    print(f"Límite superior: {limite_superior:.2f}") 