# Guide Tutoriel Complet — Projet Big Data E-commerce

> Suivez chaque etape dans l'ordre. Ne passez pas a l'etape suivante tant que la precedente n'est pas OK.

---

## ETAPE 0 — Verification de l'environnement

Ouvrez PowerShell dans le dossier du projet :

```powershell
cd C:\Users\kaabi\Desktop\bigdata
powershell -ExecutionPolicy Bypass -File scripts\check_environment.ps1
```

### Resultat sur VOTRE machine (verifie le 30/06/2026)

| Outil | Statut | Version |
|-------|--------|---------|
| Java | OK | OpenJDK 25 |
| Docker | OK | 29.6.1 |
| Docker Compose | OK | v5.1.4 |
| Python | OK | 3.14.6 |
| Maven | MANQUANT | — |

### Si Maven manque (votre cas)

**Option A — IntelliJ IDEA (recommande pour etudiant) :**
1. Ouvrir le dossier `mapreduce/` dans IntelliJ
2. IntelliJ detecte automatiquement le `pom.xml`
3. Clic droit sur `pom.xml` → Maven → Reload Project
4. Panneau Maven → Lifecycle → `package`

**Option B — Compiler via Docker (sans installer Maven) :**
```powershell
scripts\build-jar-docker.bat
```

Le JAR sera dans : `mapreduce\target\ecommerce-mapreduce-1.0-SNAPSHOT.jar`

> **Note Java :** Votre Java 25 fonctionne pour IntelliJ, mais Hadoop utilise Java 8 **dans Docker**. Pas de probleme.

---

## ETAPE 1 — Generer le dataset e-commerce (Python)

```powershell
cd C:\Users\kaabi\Desktop\bigdata
python scripts\generate_dataset.py --rows 1000
```

**Ce que fait le script :** cree un CSV avec 1000 transactions aleatoires (Phone, Laptop, Jeans...).

**Verifier :**
```powershell
python scripts\local_batch_analysis.py
```

Vous devez voir le CA global (~548 000 EUR) et le top produits.

---

## ETAPE 2 — Compiler le projet MapReduce (Java Maven)

```powershell
scripts\build-jar-docker.bat
```

**Verifier que le JAR existe :**
```powershell
dir mapreduce\target\*.jar
```

---

## ETAPE 3 — Creer le cluster Hadoop (Docker)

### 3.1 Demarrer Docker Desktop
Assurez-vous que Docker Desktop est lance (icone baleine dans la barre des taches).

### 3.2 Construire et lancer le cluster

```powershell
cd C:\Users\kaabi\Desktop\bigdata\docker\hadoop
docker compose up -d --build
```

> **Patience :** Le premier build telecharge Hadoop (~700 Mo). Comptez 10-20 minutes.

### 3.3 Verifier que les 3 conteneurs tournent

```powershell
docker ps
```

Vous devez voir :
- `hadoop-master`
- `hadoop-worker1`
- `hadoop-worker2`

### 3.4 Interfaces web

| Service | URL |
|---------|-----|
| NameNode (HDFS) | http://localhost:9870 |
| YARN (jobs) | http://localhost:8088 |

---

## ETAPE 4 — Tester HDFS

```powershell
docker exec hadoop-master hdfs dfs -ls /
docker exec hadoop-master hdfs dfs -mkdir -p /input
docker exec hadoop-master hdfs dfs -put /data/ecommerce_dataset_bigdata.csv /input/ecommerce
docker exec hadoop-master hdfs dfs -ls /input
```

**Explication simple :**
- `hdfs dfs -ls` = lister les fichiers (comme `dir` sur Windows)
- `-put` = uploader un fichier local vers HDFS
- HDFS = le "disque dur distribue" du cluster

---

## ETAPE 5 — WordCount MapReduce (premier job)

### 5.1 Creer un fichier test

```powershell
docker exec hadoop-master bash -c "echo 'hello world hello spark hello hadoop' > /tmp/test.txt"
docker exec hadoop-master hdfs dfs -put /tmp/test.txt /input/wordcount
```

### 5.2 Lancer WordCount

```powershell
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar com.bigdata.ecommerce.wordcount.WordCount /input/wordcount /output/wordcount
```

### 5.3 Voir le resultat

```powershell
docker exec hadoop-master hdfs dfs -cat /output/wordcount/part-r-00000
```

**Resultat attendu :**
```
hadoop  1
hello   3
spark   1
world   1
```

### Comprendre le code WordCount

| Fichier | Role |
|---------|------|
| `TokenizerMapper.java` | Lit chaque ligne, decoupe en mots, emet (mot, 1) |
| `IntSumReducer.java` | Regroupe par mot, somme les 1 |
| `WordCount.java` | Configure et lance le job |

---

## ETAPE 6 — Analyse Batch E-commerce (MapReduce)

### 6.1 Lancer tous les jobs

```powershell
docker exec hadoop-master hdfs dfs -rm -r -f /output/ecommerce
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar com.bigdata.ecommerce.EcommerceBatchAnalysis /input/ecommerce /output/ecommerce
```

### 6.2 Consulter les resultats

```powershell
# CA global
docker exec hadoop-master hdfs dfs -cat /output/ecommerce/global-revenue/part-r-00000

# CA par produit
docker exec hadoop-master hdfs dfs -cat /output/ecommerce/revenue-by-product/part-r-*

# Ventes par categorie
docker exec hadoop-master hdfs dfs -cat /output/ecommerce/sales-by-category/part-r-*

# Top produits
docker exec hadoop-master hdfs dfs -cat /output/ecommerce/top-products/part-r-*
```

### 6.3 Jobs individuels (si besoin)

```powershell
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar com.bigdata.ecommerce.revenue.RevenueByProduct /input/ecommerce /output/revenue
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar com.bigdata.ecommerce.category.SalesByCategory /input/ecommerce /output/category
docker exec hadoop-master hadoop jar /apps/ecommerce-mapreduce.jar com.bigdata.ecommerce.topproducts.TopProducts /input/ecommerce /output/top
```

---

## ETAPE 7 — Cluster Spark (Docker)

```powershell
cd C:\Users\kaabi\Desktop\bigdata\docker\spark
docker compose up -d
```

**Verifier :**
```powershell
docker ps
# spark-master, spark-worker1, spark-worker2
```

**Interface Spark :** http://localhost:8080

---

## ETAPE 8 — Spark RDD (transformations + actions)

```powershell
docker exec spark-master spark-submit /workspace/spark/rdd_demo.py
```

**Ce que vous apprenez :**

| Operation | Type | Exemple |
|-----------|------|---------|
| textFile | creation RDD | charger CSV |
| flatMap | transformation | decouper lignes |
| map | transformation | calculer CA |
| filter | transformation | garder Electronics |
| reduceByKey | transformation | agreger par produit |
| collect / take | action | afficher resultats |

### Spark Shell (interactif)

```powershell
docker exec -it spark-master spark-shell
```

Puis dans le shell :
```scala
val rdd1 = sc.textFile("/workspace/ecommerce_dataset_bigdata.csv")
val rdd2 = rdd1.flatMap(line => line.split(","))
rdd2.take(10)
```

---

## ETAPE 9 — Spark Streaming (temps reel)

### Terminal 1 — Lancer le streaming

```powershell
docker exec spark-master spark-submit /workspace/spark/streaming_ecommerce.py /workspace/stream_input /workspace/stream_checkpoint
```

### Terminal 2 — Simuler le flux de ventes

```powershell
cd C:\Users\kaabi\Desktop\bigdata
python scripts\generate_stream_data.py --output stream_input --batch-size 30 --interval 5
```

**Ce qui se passe :**
1. Python ecrit un nouveau CSV toutes les 5 secondes dans `stream_input/`
2. Spark detecte le nouveau fichier et l'analyse
3. Affichage du top produits en fenetre glissante
4. Si > 100 ventes par batch → `ALERTE: pic de ventes`

---

## ETAPE 10 — Rapport final

Le rapport est pret dans : `docs/RAPPORT_FINAL.md`

**A personnaliser :**
- Votre nom
- Captures d'ecran des interfaces (9870, 8080, 8088)
- Resultats MapReduce
- Conclusion personnelle

**Exporter en PDF :** Ouvrir dans VS Code / Word → Exporter en PDF.

---

## Depannage (erreurs frequentes)

| Erreur | Solution |
|--------|----------|
| `mvn not found` | Utiliser `scripts\build-jar-docker.bat` ou Maven IntelliJ |
| `Cannot connect to Docker` | Lancer Docker Desktop |
| `JAR not found` dans conteneur | Compiler AVANT `docker compose up` |
| `Output directory already exists` | `hdfs dfs -rm -r /output/xxx` avant de relancer |
| Build Hadoop tres long | Normal la 1ere fois (telechargement Hadoop) |
| Port 9870 deja utilise | Arreter un ancien conteneur : `docker stop hadoop-master` |

### Arreter les clusters

```powershell
cd docker\hadoop && docker compose down
cd docker\spark && docker compose down
```

### Redemarrer les clusters

```powershell
docker start hadoop-master hadoop-worker1 hadoop-worker2
docker start spark-master spark-worker1 spark-worker2
```

---

## Checklist de rendu

- [ ] Dataset CSV genere
- [ ] JAR MapReduce compile
- [ ] Cluster Hadoop demarre (capture 9870)
- [ ] WordCount execute avec resultat
- [ ] 4 jobs e-commerce executes
- [ ] Cluster Spark demarre (capture 8080)
- [ ] RDD demo execute
- [ ] Streaming avec alertes
- [ ] Rapport final (`docs/RAPPORT_FINAL.md`)

---

*Bon courage ! Revenez me voir si vous bloquez sur une etape precise.*
