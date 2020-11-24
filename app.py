from flask import Flask
import pandas as pd
import mysql.connector
from sklearn.neighbors import NearestNeighbors
import json

def recomendacao(id_usuario):
  host="dbtcc.cknsdqa3n4oo.sa-east-1.rds.amazonaws.com"
  port=3306
  dbname="DB_TCC"
  user="tccleitura"
  password="afvD7pzxkA23"

  conn = mysql.connector.connect(user=user, password=password,
                              host=host,
                              database=dbname)

  cur = conn.cursor()
  cur.execute('select * from questions where ID_USUARIO = %i' %id_usuario)
  dados = cur.fetchall()

  if dados==[]:
    return {"parametros": ""}

  cur.execute('select * from questions')
  dados = cur.fetchall()
  dataset = pd.DataFrame(dados, columns=['ID', 'USUARIO', 'LIVRO', 'TITULO', 'RATING','D1','D2'])[['USUARIO','LIVRO','TITULO','RATING']]

  movies_features = dataset.pivot_table(index='USUARIO', columns='TITULO', values='RATING').fillna(0)

  modelo = NearestNeighbors(metric='cosine', n_neighbors=3)
  modelo.fit(movies_features)

  distancia, indices_vizinhos = modelo.kneighbors(movies_features.loc[id_usuario].values.reshape(1,-1), n_neighbors=4)

  parametros = {}

  for i in range(0, len(distancia.flatten())):
    if movies_features.index[indices_vizinhos.flatten()[i]] != id_usuario:
      parametros[str(movies_features.index[indices_vizinhos.flatten()[i]])] = distancia.flatten()[i]

  id_recomendado = movies_features.index[indices_vizinhos.flatten()][1]
  base = movies_features.loc[id_usuario].to_frame()
  recomendado = movies_features.loc[id_recomendado].to_frame()

  novos_titulos = pd.merge(base,recomendado,on='TITULO',how='inner')
  novos_titulos = novos_titulos[(novos_titulos[id_recomendado] > 0) & (novos_titulos[id_usuario] == 0)].reset_index()

  livros = json.loads(novos_titulos.to_json(force_ascii=False))
  parametros["livros"] = livros

  resultado_recomendacao = {"parametros":parametros}
  return resultado_recomendacao

app = Flask(__name__)


@app.route("/recomendar/<idUsuario>")
def recomendar(idUsuario):
    idUsuario = int(idUsuario)
    return recomendacao(idUsuario)


if __name__ == '__main__':
    app.run()
