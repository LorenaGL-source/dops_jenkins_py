import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os



# --- Parámetros de conexión PostgreSQL ---
DB_HOST = os.getenv('DB_HOST','postgres')
DB_PORT = os.getenv('DB_PORT','5432')
DB_NAME = os.getenv('DB_NAME','pagila')
DB_USER = os.getenv('DB_USER','postgres')
DB_PASS = os.getenv('DB_PASS','lorena2908') # Reemplaza por la contraseña que usas

def extract_data():
    try:
        # Conexión con PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        conn.set_client_encoding('WIN1252')
        # Cursor para lectura segura
        cur = conn.cursor()

        # Clientes con bajo uso y pagos fallidos
        cur.execute("""SELECT cu.customer_id, cu.first_name || ' ' || cu.last_name AS name,
           MAX(r.rental_date) AS last_rental,
           COUNT(r.rental_id) FILTER (WHERE r.rental_date > (SELECT MAX(rental_date) FROM rental) - INTERVAL '90 days') AS recent_rentals,
           COUNT(p.payment_id) FILTER (WHERE p.amount = 0) AS failed_payments
    	FROM customer cu
    	LEFT JOIN rental r ON r.customer_id = cu.customer_id
    	LEFT JOIN payment p ON p.customer_id = cu.customer_id
    	GROUP BY cu.customer_id, name
    	HAVING COUNT(r.rental_id) > 0;
    	""")
        df_churn = cur.fetchall()
        df_churn_columns = [desc[0] for desc in cur.description]
        df_churn = pd.DataFrame(df_churn, columns=df_churn_columns)

        # Extraer pagos
        cur.execute("""SELECT f.film_id, f.title, c.name AS category,
           		COUNT(r.rental_id) AS rentals_90d,
          		SUM(p.amount) AS revenue
    		FROM film f
    	JOIN film_category fc ON fc.film_id = f.film_id
    	JOIN category c ON c.category_id = fc.category_id
    	LEFT JOIN inventory i ON i.film_id = f.film_id
    	LEFT JOIN rental r ON r.inventory_id = i.inventory_id
   	 LEFT JOIN payment p ON p.rental_id = r.rental_id
    	WHERE r.rental_date > (SELECT MAX(rental_date) FROM rental) - INTERVAL '90 days'
    	GROUP BY f.film_id, f.title, c.name
    	HAVING COUNT(r.rental_id) < 5
   	ORDER BY rentals_90d ASC, revenue ASC
    	LIMIT 10;
    	""")
        df_movies = cur.fetchall()
        payment_columns = [desc[0] for desc in cur.description]
        df_movies  = pd.DataFrame(df_movies, columns=payment_columns)

 	# 3. Rentabilidad por categoría
        cur.execute("""
    		WITH max_date AS (
  		SELECT MAX(rental_date) AS max_rental_date FROM rental
		)
		SELECT c.name AS category,
      			 COUNT(r.rental_id) AS total_rentals,
       			SUM(p.amount) AS total_revenue
		FROM category c
		JOIN film_category fc ON fc.category_id = c.category_id
		JOIN film f ON f.film_id = fc.film_id
		JOIN inventory i ON i.film_id = f.film_id
		JOIN rental r ON r.inventory_id = i.inventory_id
		JOIN payment p ON p.rental_id = r.rental_id
		JOIN max_date m ON true
		WHERE r.rental_date > m.max_rental_date - INTERVAL '90 days'
		GROUP BY c.name
		ORDER BY total_revenue DESC;
    		""")
        df_revenue_cat = cur.fetchall()
        payment_columns = [desc[0] for desc in cur.description]
        df_revenue_cat  = pd.DataFrame(df_revenue_cat, columns=payment_columns)

        cur.close()
        conn.close()

        print("Extracción completada.")
        return df_churn,df_movies,df_revenue_cat

    except Exception as e:
        print("❌ Error en la extracción:", e)
        return pd.DataFrame(), pd.DataFrame()

def transform_data(df_churn):
    # Asegurar fechas sin zona horaria
    df_churn['last_rental'] = pd.to_datetime(df_churn['last_rental']).dt.tz_localize(None)

    # Scoring simple de abandono
    df_churn['days_since_last_rental'] = (pd.Timestamp.today() - df_churn['last_rental']).dt.days
    df_churn['churn_score'] = (
        df_churn['days_since_last_rental'] / 90 +
        df_churn['failed_payments'] * 0.5 -
        df_churn['recent_rentals'] * 0.3
    )
    df_churn = df_churn.sort_values(by='churn_score', ascending=False).head(10)
    return df_churn

def generate_pdf(df_churn, df_movies, df_revenue_cat, output_file='output/reporte_pagila.pdf'):
    with PdfPages(output_file) as pdf:

        # 1. Gráfico: Clientes en riesgo
        if not df_churn.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df_churn['name'], df_churn['churn_score'], color='tomato')
            plt.xlabel('Puntaje de abandono')
            plt.title('Top 10 Clientes con Mayor Riesgo de Abandono')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            pdf.savefig()
            plt.close()

            # Tabla de detalle
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis('off')
            ax.axis('tight')
            table_data = df_churn[['name', 'days_since_last_rental', 'recent_rentals', 'failed_payments']]
            ax.table(cellText=table_data.values, colLabels=table_data.columns, loc='center')
            plt.title("Detalle de Clientes en Riesgo")
            pdf.savefig()
            plt.close()
        else:
            print("⚠️ No hay datos de churn para mostrar.")

        # 2. Gráfico: Películas poco rentables
        if not df_movies.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df_movies['title'], df_movies['revenue'], color='gray')
            plt.xlabel('Ingresos en 90 días')
            plt.title('Películas con Baja Rentabilidad')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            pdf.savefig()
            plt.close()

            # Tabla de detalle
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis('off')
            ax.axis('tight')
            table_data = df_movies[['title', 'category', 'rentals_90d', 'revenue']]
            ax.table(cellText=table_data.values, colLabels=table_data.columns, loc='center')
            plt.title("Detalle de Películas con Baja Rentabilidad")
            pdf.savefig()
            plt.close()
        else:
            print("⚠️ No hay películas poco rentables para mostrar.")

        # 3. Gráfico: Rentabilidad por categoría
        if not df_revenue_cat.empty:
            plt.figure(figsize=(10, 6))
            plt.bar(df_revenue_cat['category'], df_revenue_cat['total_revenue'], color='seagreen')
            plt.title('Rentabilidad por Categoría (últimos 90 días)')
            plt.ylabel('Ingresos ($)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            pdf.savefig()
            plt.close()

            # Tabla de detalle
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis('off')
            ax.axis('tight')
            table_data = df_revenue_cat[['category', 'total_rentals', 'total_revenue']]
            ax.table(cellText=table_data.values, colLabels=table_data.columns, loc='center')
            plt.title("Detalle: Rentabilidad por Categoría")
            pdf.savefig()
            plt.close()
        else:
            print("⚠️ No hay datos de rentabilidad por categoría.")

def main():
    print("🔄 Ejecutando ETL...")
    df_churn, df_movies, df_revenue_cat = extract_data()
    df_churn = transform_data(df_churn)
    generate_pdf(df_churn, df_movies, df_revenue_cat)
    print("✅ Reporte generado: output/reporte_pagila.pdf")

if __name__ == '__main__':
    main()