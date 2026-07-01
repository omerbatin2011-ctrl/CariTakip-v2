# Git Kurulum ve Kullanım Rehberi

## 1. Git kurulumu

Git for Windows kurulur. Kurulumda şu seçenek seçilmeli:

**Git from the command line and also from 3rd-party software**

Kurulumdan sonra CMD kapatılıp yeniden açılır.

Kontrol:

```cmd
git --version
```

## 2. İlk kayıt

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
git init
git add .
git commit -m "v130 git hazir kararlı sürüm"
git tag v130
```

## 3. Her yeni çalışan sürümde

```cmd
git add .
git commit -m "v131 açıklama"
git tag v131
```

## 4. Eski sürüme dönme

```cmd
git checkout v130
```

Tekrar geliştirme dalına dönmek için:

```cmd
git checkout master
```

Bazı Git sürümlerinde ana dal adı `main` olabilir:

```cmd
git checkout main
```

## 5. GitHub'a gönderme

GitHub'da boş repo oluşturduktan sonra:

```cmd
git remote add origin REPO_ADRESI
git branch -M main
git push -u origin main --tags
```
