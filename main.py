

from __future__ import annotations
import json, re, statistics, traceback, csv
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional

DB_FILE = Path("watchlist_db.json")

class MovieDB:
    def __init__(self):
        self.movies: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        try:
            if DB_FILE.exists():
                self.movies = json.loads(DB_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError) as e:
            print("[Błąd] Nie można wczytać bazy:", e)
            self.movies = []

    def save(self):
        try:
            DB_FILE.write_text(json.dumps(self.movies, ensure_ascii=False, indent=2), encoding="utf-8")
        except IOError as e:
            print("[Błąd] Nie można zapisać bazy:", e)

    def add(self, m: Dict[str, Any]):
        self.movies.append(m); self.save()

    def update(self, idx: int, data: Dict[str, Any]):
        if 0<=idx< len(self.movies):
            self.movies[idx].update(data); self.save()
        else:
            raise IndexError("Niepoprawny indeks")

    def delete(self, idx:int):
        try:
            del self.movies[idx]; self.save()
        except IndexError:
            raise

    def search(self,q:str):
        pat=re.compile(re.escape(q),re.I)
        return [m for m in self.movies if pat.search(m['title'])]

    def sort_by(self,key:str,rev=False):
        self.movies.sort(key=lambda m:m.get(key) or "",reverse=rev)

    def stats(self):
        genres=Counter(m['genre'] for m in self.movies)
        ratings=[m['rating'] for m in self.movies if m['rating'] is not None]
        avg=statistics.mean(ratings) if ratings else 0
        best=max(self.movies,key=lambda m:m['rating'] or 0,default=None)
        return genres,avg,best

def prompt(msg:str,allow_empty=False):
    while True:
        val=input(msg).strip()
        if val or allow_empty: return val
        print("Pole nie może być puste.")

def input_int(msg:str,allow_empty=False,mini=None,maxi=None):
    while True:
        val=input(msg).strip()
        if not val and allow_empty: return None
        try:
            i=int(val)
            if (mini is not None and i<mini) or (maxi is not None and i>maxi):
                print(f"Podaj liczbę z zakresu {mini}-{maxi}")
                continue
            return i
        except ValueError:
            print("Podaj liczbę całkowitą.")

def add_movie(db:MovieDB):
    data={}
    data['title']=prompt("Tytuł: ")
    data['director']=prompt("Reżyser: ",True)
    data['year']=input_int("Rok produkcji: ",True)
    data['genre']=prompt("Gatunek: ",True)
    status=prompt("Status (obejrzany/nieobejrzany): ",True)
    data['status']=status if status else 'nieobejrzany'
    data['rating']=input_int("Ocena 0-10: ",True,0,10)
    data['description']=prompt("Opis: ",True)
    data['watched_on']=datetime.now().isoformat() if data['status'].lower().startswith('obej') else None
    db.add(data)
    print("[OK] Dodano film")

def list_movies(db:MovieDB, items:Optional[List[Dict[str,Any]]]=None):
    items=items if items is not None else db.movies
    if not items:
        print("(pusto)"); return
    print("# | Tytuł (rok) [ocena] - gatunek, status")
    for i,m in enumerate(items):
        print(f"{i:2d}| {m['title']} ({m.get('year','?')}) [{m.get('rating','-')}] - {m.get('genre','')} , {m.get('status','')}")

def edit_movie(db:MovieDB):
    list_movies(db)
    idx=input_int("Podaj # filmu do edycji: ")
    try:
        movie=db.movies[idx]
    except IndexError:
        print("Błędny indeks"); return
    print("[Enter] aby zostawić bez zmian")
    for field in ('title','director','year','genre','status','rating','description'):
        if field=='year':
            val=input_int(f"{field} ({movie.get(field)}): ",True)
        elif field=='rating':
            val=input_int(f"{field} ({movie.get(field)}): ",True,0,10)
        else:
            val=prompt(f"{field} ({movie.get(field)}): ",True)
        if val!=None and val!='':
            movie[field]=val
    if movie['status'].lower().startswith('obej') and not movie.get('watched_on'):
        movie['watched_on']=datetime.now().isoformat()
    db.save(); print("[OK] Zaktualizowano")

def delete_movie(db:MovieDB):
    list_movies(db)
    idx=input_int("Podaj # filmu do usunięcia: ")
    try:
        db.delete(idx); print("[OK] Usunięto")
    except IndexError:
        print("Błędny indeks")

def export_movies(db:MovieDB):
    path=prompt("Plik docelowy [.txt]: ") or "export.txt"
    try:
        with open(path,'w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f,delimiter='\t')
            writer.writerow(db.movies[0].keys() if db.movies else [])
            for m in db.movies:
                writer.writerow(m.values())
        print("[OK] Eksportowano do",path)
    except IOError as e:
        print("Błąd zapisu:",e)

def show_stats(db:MovieDB):
    if not db.movies:
        print("Brak danych"); return
    genres,avg,best=db.stats()
    print("-- Statystyki --")
    print("Liczba filmów:",len(db.movies))
    print("Średnia ocena:",round(avg,2))
    if best: print("Najlepiej oceniany:",best['title'],best['rating'])
    print("Filmy wg gatunku:")
    for g,c in genres.items():
        print(f" {g}: {c}")
    ratings=[m['rating'] for m in db.movies if m['rating'] is not None]
    if ratings:
        print("Histogram ocen:")
        for r in range(1,11):
            bar='█'*ratings.count(r)
            print(f"{r:2d}: {bar}")
    ans=prompt("Pokazać wykresy matplotlib? (t/n): ")
    if ans.lower().startswith('t'):
        try:
            import matplotlib.pyplot as plt
            plt.figure(); plt.bar(genres.keys(),genres.values()); plt.title('Filmy wg gatunku')
            plt.figure(); plt.hist(ratings,bins=range(1,12),edgecolor='black',align='left'); plt.title('Rozkład ocen')
            plt.figure(); plt.bar(['Średnia',best['title']], [avg,best['rating']]); plt.ylim(0,10); plt.title('Średnia vs najlepszy')
            plt.show()
        except ImportError:
            print("Brak matplotlib")

def main():
    db=MovieDB()
    menu={
        '1':("Dodaj film",add_movie),
        '2':("Wyświetl kolekcję",lambda db: list_movies(db)),
        '3':("Szukaj (część tytułu)",lambda db: list_movies(db, db.search(prompt('Szukaj: ')))),
        '4':("Edytuj film",edit_movie),
        '5':("Usuń film",delete_movie),
        '6':("Eksport do pliku",export_movies),
        '7':("Statystyki",show_stats),
        '0':("Wyjście",None)
    }
    while True:
        print("\n===== WATCHLIST =====")
        for k,(desc,_) in menu.items():
            print(f"{k}. {desc}")
        choice=input("Wybierz opcję: ").strip()
        if choice=='0': break
        action=menu.get(choice,(None,None))[1]
        if action:
            try:
                action(db)
            except Exception as e:
                traceback.print_exc()
                print("Błąd:",e)
        else:
            print("Niepoprawna opcja")

if __name__=='__main__':
    main()
