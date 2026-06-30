# Rapport Final — Projet Big Data
## Analyse des transactions e-commerce en Batch et Streaming

**Etudiant :** [Votre nom]  
**Date :** Juin 2026  
**Technologies :** Hadoop MapReduce, Apache Spark, Docker, Java Maven, Python

---

## 1. Introduction

L'e-commerce genere des millions de transactions par jour. Pour analyser ces donnees, les entreprises utilisent des architectures **Big Data** combinant :

- le **traitement batch** (analyse historique sur de gros volumes),
- le **traitement streaming** (detection en temps reel des tendances et anomalies).

Ce projet met en pratique ces deux approches sur un dataset de **1000 transactions e-commerce**.

---

## 2. Objectifs

| Objectif | Statut |
|----------|--------|
| Cluster Hadoop Docker (1 master + 2 workers) | Realise |
| Test HDFS (upload/download) | Realise |
| WordCount MapReduce (Java Maven) | Realise |
| Dataset e-commerce (Python) | Realise |
| Analyse batch (CA, categories, top produits) | Realise |
| Cluster Spark Docker | Realise |
| RDD + Streaming Spark | Realise |
| Detection de pics de ventes | Realise |

---

## 3. Architecture

```
                    +---------------------------+
                    | ecommerce_dataset.csv     |
                    | (1000 transactions)       |
                    +-------------+-------------+
                                  |
            +---------------------+---------------------+
            |                                           |
   +--------v---------+                      +----------v---------+
   | Hadoop MapReduce |                      | Apache Spark       |
   | (Batch)          |                      | (RDD + Streaming)  |
   | HDFS + YARN      |                      | Structured Stream  |
   +--------+---------+                      +----------+---------+
            |                                           |
   +--------v---------+                      +----------v---------+
   | Resultats batch  |                      | Resultats temps    |
   | - CA global      |                      | reel               |
   | - CA/produit     |                      | - Top produits     |
   | - Ventes/categ.  |                      | - Alertes pics     |
   | - Top produits   |                      |                    |
   +------------------+                      +--------------------+
```

### Composants Docker

| Service | Role | Ports |
|---------|------|-------|
| hadoop-master | NameNode + ResourceManager | 9870, 8088, 9000 |
| hadoop-worker1/2 | DataNode + NodeManager | — |
| spark-master | Spark Master | 8080, 7077 |
| spark-worker1/2 | Spark Workers (4 cores chacun) | — |

---

## 4. Dataset

### Schema

| Colonne | Type | Description |
|---------|------|-------------|
| transaction_id | int | Identifiant unique |
| date | datetime | Date de la vente |
| product | string | Nom du produit |
| category | string | Categorie |
| price | float | Prix unitaire (EUR) |
| quantity | int | Quantite vendue |
| client_id | int | Identifiant client |

### Generation (Python)

```bash
python scripts/generate_dataset.py --rows 1000
```

### Statistiques (analyse locale)

| Indicateur | Valeur |
|------------|--------|
| Chiffre d'affaires global | **548 445 EUR** |
| Nombre de transactions | 1000 |
| Categories | Electronics, Clothing, Education, Accessories |

**Top produits par chiffre d'affaires :**

| Produit | CA (EUR) |
|---------|----------|
| Laptop | 235 200 |
| Phone | 214 400 |
| Headphones | 37 500 |
| Shoes | 22 050 |

**Ventes par categorie :**

| Categorie | Quantite |
|-----------|----------|
| Clothing | 756 |
| Electronics | 714 |
| Education | 281 |
| Accessories | 263 |

---

## 5. Partie Batch — Hadoop MapReduce

### 5.1 Principe MapReduce

1. **Map** : lit chaque ligne, produit des paires (cle, valeur)
2. **Shuffle** : regroupe par cle
3. **Reduce** : agrege les valeurs

### 5.2 WordCount (exemple de base)

| Composant | Role |
|-----------|------|
| TokenizerMapper | decoupe le texte en mots → (mot, 1) |
| IntSumReducer | somme les occurrences |

### 5.3 Jobs e-commerce

#### Job 1 — Chiffre d'affaires par produit

- **Mapper** : cle = `product`, valeur = `price × quantity`
- **Reducer** : somme des revenus

#### Job 2 — Ventes par categorie

- **Mapper** : cle = `category`, valeur = `quantity`
- **Reducer** : somme des quantites

#### Job 3 — Top produits

- **Mapper** : cle = `product`, valeur = `quantity`
- **Reducer** : somme → tri decroissant

#### Job 4 — CA global

- **Mapper** : cle = `TOTAL_REVENUE`, valeur = `price × quantity`
- **Reducer** : somme totale

### 5.4 Commandes d'execution

```bash
# Compiler
cd mapreduce && mvn clean package

# Lancer cluster
cd docker/hadoop && docker compose up -d --build

# Upload HDFS
docker exec hadoop-master hdfs dfs -mkdir -p /input
docker exec hadoop-master hdfs dfs -put /data/ecommerce_dataset_bigdata.csv /input/ecommerce

# Executer tous les jobs
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar \
  com.bigdata.ecommerce.EcommerceBatchAnalysis /input/ecommerce /output/ecommerce
```

---

## 6. Partie Streaming — Apache Spark

### 6.1 RDD — Transformations et actions

| Operation | Type | Description |
|-----------|------|-------------|
| textFile() | creation | charge le CSV |
| flatMap() | transformation | split par virgule |
| map() | transformation | calcule le CA |
| filter() | transformation | filtre Electronics |
| reduceByKey() | transformation | agrege par produit |
| collect() / take() | action | retourne resultats |

### 6.2 Structured Streaming

Le script `streaming_ecommerce.py` :

1. surveille le dossier `stream_input/` pour de nouveaux CSV,
2. agrege les ventes par produit en **fenetre glissante** (1 min / 30 s),
3. affiche le top produits en direct,
4. declenche une **alerte** si > 100 unites vendues par batch.

### 6.3 Simulation temps reel

```bash
python scripts/generate_stream_data.py --output stream_input --batch-size 30 --interval 5
```

---

## 7. Resultats et interpretation

### Batch (historique)

- **Laptop et Phone** dominent le chiffre d'affaires (produits a forte valeur).
- **Clothing** domine en volume unitaire (produits bon marche, forte rotation).
- L'analyse batch permet de planifier stocks et campagnes marketing.

### Streaming (temps reel)

- Detection immediate des pics de ventes (Black Friday, promotions).
- Alertes automatiques pour reapprovisionnement urgent.
- Tableaux de bord live pour les equipes commerciales.

---

## 8. Difficultes rencontrees et solutions

| Probleme | Solution |
|----------|----------|
| Maven non installe | Utiliser Maven integre IntelliJ ou `mvnw` |
| Java 25 vs Hadoop Java 8 | Compiler en Java 8 dans IntelliJ ; Docker utilise Java 8 |
| JAR absent au demarrage Docker | Compiler avec `mvn package` avant `docker compose up` |
| Chemins Windows | Utiliser Docker volumes, executer commandes dans le conteneur |

---

## 9. Conclusion

Ce projet demontre une architecture Big Data complete :

- **Hadoop MapReduce** pour l'analyse historique distribuee sur HDFS,
- **Apache Spark** pour le traitement interactif (RDD) et le temps reel (Streaming),
- **Docker** pour simuler un cluster industriel en local.

Les resultats confirment que l'approche hybride batch + streaming est essentielle pour une plateforme e-commerce moderne : comprendre le passe tout en reagissant en temps reel.

---

## 10. Annexes

### Structure du projet

```
bigdata/
├── ecommerce_dataset_bigdata.csv
├── mapreduce/          → Jobs Java MapReduce
├── spark/              → Scripts Python/Scala
├── docker/hadoop/      → Cluster Hadoop
├── docker/spark/       → Cluster Spark
├── scripts/            → Utilitaires Python
└── docs/               → Documentation
```

### References

- Apache Hadoop Documentation — https://hadoop.apache.org
- Apache Spark Documentation — https://spark.apache.org
- Docker Documentation — https://docs.docker.com

---

*Fin du rapport*
