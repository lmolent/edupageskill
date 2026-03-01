# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "python-dotenv>=0.9.9",
#     "edupage-api>=0.12.3",
#     "html2text>=2025.4.15",
# ]
# ///
import os
import datetime
import json
import ast
import argparse
from dotenv import load_dotenv
from edupage_api import Edupage
from edupage_api.people import EduStudent, Gender
from edupage_api.dbi import DbiHelper
import html2text

def get_credentials():
    """Loads credentials from the .env file."""
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    
    if not all([username, password]):
        raise ValueError(
            "Chýbajúce prihlasovacie údaje (USERNAME, PASSWORD).\n"
            "TIP: Vytvor súbor .env podľa .env.example alebo použi 'clawhub setup' na konfiguráciu."
        )
        
    return username, password

def get_calculated_grade(edu_grade):
    """Attempts to calculate the actual grade from percentage if more_details contains evaluation criteria."""
    if edu_grade.max_points and edu_grade.percent is not None:
        try:
            for detail in (edu_grade.more_details or []):
                # Edupage often stores evaluation criteria as a string representation of a dict
                try:
                    data = ast.literal_eval(detail)
                except:
                    continue
                
                if isinstance(data, dict) and 'vyhodnotenie' in data:
                    eval_data = data['vyhodnotenie']
                    if 'hodnoty' in eval_data:
                        # Sort by threshold ascending
                        thresholds = sorted(eval_data['hodnoty'], key=lambda x: float(x.get('do', 100)))
                        for thresh in thresholds:
                            if edu_grade.percent <= float(thresh.get('do', 100)):
                                return thresh.get('znamka')
        except:
            pass
    return None

def show_timetable(edupage_instance, student_id=None, target_date=None):
    """Fetches and prints the timetable for a specific date or today/next Monday."""
    print("\n[ROZVRH HODÍN]")
    
    if target_date:
        fetch_date = target_date
    else:
        today = datetime.date.today()
        fetch_date = today
        # Ak je víkend a nebol zadaný konkrétny dátum, skúsme pondelok
        if today.weekday() == 5: # Sobota
            fetch_date = today + datetime.timedelta(days=2)
            print(f"(Dnes je sobota, načítavam rozvrh na pondelok {fetch_date.strftime('%d.%m.%Y')})")
        elif today.weekday() == 6: # Nedeľa
            fetch_date = today + datetime.timedelta(days=1)
            print(f"(Dnes je nedeľa, načítavam rozvrh na pondelok {fetch_date.strftime('%d.%m.%Y')})")
    
    timetable = None
    try:
        timetable = edupage_instance.get_my_timetable(fetch_date)
    except Exception:
        if student_id:
            try:
                student = EduStudent(
                    person_id=int(student_id),
                    name="",
                    gender=Gender.MALE,
                    in_school_since=None,
                    class_id=0,
                    number_in_class=0
                )
                timetable = edupage_instance.get_timetable(student, fetch_date)
            except Exception as e:
                 print(f"Nepodarilo sa načítať rozvrh. (Detail: {e})")
                 return
        else:
            print(f"Nepodarilo sa načítať rozvrh.")
            return

    print(f"Dátum: {fetch_date.strftime('%A, %d.%m.%Y')}")
    
    if not timetable or not timetable.lessons:
        print("     Žiadne hodiny na tento deň.")
        return
        
    for lesson in timetable.lessons:
        subject_name = lesson.subject.name if lesson.subject else "N/A"
        teacher_name = lesson.teachers[0].name if lesson.teachers and len(lesson.teachers) > 0 else "N/A"
        classroom = lesson.classrooms[0].name if lesson.classrooms and len(lesson.classrooms) > 0 else "-"
        status = "(Odpadla)" if lesson.is_cancelled else ""

        print(f"  {lesson.start_time}-{lesson.end_time}: {subject_name:<20} {teacher_name:<20} [{classroom}] {status}")

def show_grades(edupage_instance):
    """Fetches and prints the latest grades."""
    print("\n[POSLEDNÉ ZNÁMKY]")
    try:
        grades = edupage_instance.get_grades()
    except Exception as e:
        print(f"Nepodarilo sa načítať známky. (Detail: {e})")
        return

    if not grades:
        print("     Nenašli sa žiadne známky.")
        return

    sorted_grades = sorted(grades, key=lambda x: x.date, reverse=True)

    for grade in sorted_grades[:10]:
        date_str = grade.date.strftime('%d.%m.%Y')
        subject = grade.subject_name if grade.subject_name else "N/A"
        
        value = str(grade.grade_n)
        display_grade = value
        
        # If it's a point-based grade, try to find the actual grade (1-5)
        calculated = get_calculated_grade(grade)
        if calculated:
            display_grade = f"{calculated} ({value}b / {int(grade.max_points)}b)"
        elif grade.max_points:
            display_grade = f"{value}b / {int(grade.max_points)}b"
            
        if grade.verbal:
            display_grade = "Slovné"
        
        comment = f" [{grade.comment}]" if grade.comment else ""
        title = f" - {grade.title}" if grade.title else ""
        print(f"  {date_str} | {subject:<20} | Známka: {display_grade:<12} {title}{comment}")

def show_notifications(edupage_instance):
    """Fetches and prints the latest notifications."""
    print("\n[NAJNOVŠIE OZNAMY]")
    try:
        notifications = edupage_instance.get_notifications()
    except Exception as e:
        print(f"Nepodarilo sa načítať oznamy. (Detail: {e})")
        return

    if not notifications:
        print("     Nenašli sa žiadne oznamy.")
        return
        
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.body_width = 100

    for i, notification in enumerate(notifications[:5]):
        author_name = str(notification.author)
        event_date = notification.timestamp.strftime('%d.%m.%Y %H:%M') if notification.timestamp else "N/A"
        
        print(f"\n--- {i+1}. {author_name} ({event_date}) ---")
        plain_text = h.handle(notification.text)
        print(plain_text.strip())

def show_my_lunch(edupage_instance, student_id, target_date=None):
    """Fetches and prints the ordered lunch for a specific date."""
    print("\n🍽️ OBJEDNANÝ OBED")
    
    if not target_date:
        target_date = datetime.date.today()
    
    print(f"\n📅 Obed pre: {target_date.strftime('%d.%m.%Y')} ({target_date.strftime('%A')})")
    
    # Ošetrenie víkendov - jedlo nie je dostupné
    if target_date.weekday() >= 5:  # 5 = Sobota, 6 = Nedeľa
        print("\n❌ Žiadne jedlo pre víkendové dni.")
        return
    
    try:
        # Načítame jedlá pre daný deň
        meals = edupage_instance.get_meals(target_date)
        
        if not meals:
            print("\n❌ Žiadne jedlá pre tento deň.")
            return
        
        # Získame obed (lunch je Meal objekt)
        lunch = getattr(meals, 'lunch', None)
        
        if not lunch:
            print("\n❌ Žiadne jedlo pre tento deň.")
            return
        
        # Získame ID objednaného jedla (môže byť číslo alebo písmeno ako 'X')
        ordered_menu_id = getattr(lunch, 'ordered_meal', None)
        
        if not ordered_menu_id or ordered_menu_id == 'X':
            print("\n❌ Žiadny objednaný obed")
            return
        
        # Získame zoznam menu
        menus = getattr(lunch, 'menus', [])
        
        # Nájdeme objednané jedlo - hľadáme podľa number (môže byť číslo alebo písmeno)
        ordered_item = None
        for menu in menus:
            menu_number = str(getattr(menu, 'number', ''))
            if menu_number == str(ordered_menu_id):
                ordered_item = menu
                break
        
        if not ordered_item:
            # Špeciálna logika pre pondelok (02.03.2026) - ordered_menu_id='X'
            # V zozname menu sa 'X' zobrazuje ako 'None'
            if ordered_menu_id == 'X':
                for menu in menus:
                    menu_number = str(getattr(menu, 'number', ''))
                    # Hľadáme menu s number='None' alebo prázdne string
                    if menu_number == 'None' or menu_number == '':
                        ordered_item = menu
                        break
            
            if not ordered_item:
                print(f"\n❌ Objednané jedlo s ID '{ordered_menu_id}' nebolo nájdené v zozname menu.")
                print(f"   Dostupné menu: {[str(getattr(m, 'number', 'N/A')) for m in menus]}")
                return
        
        meal_name = getattr(ordered_item, 'name', 'Neznáme')
        meal_type = lunch.meal_type.name if hasattr(lunch, 'meal_type') and lunch.meal_type else "N/A"
        
        print(f"\n🍽️ Typ: {meal_type}")
        print(f"🍲 Jedlo: {meal_name}")
        
        # Pokúsime sa zobrazit číslo menu pre lepšiu čitateľnosť
        if ordered_menu_id != 'X':
            print(f"✅ Objednané jedlo: {ordered_menu_id}")
            
    except Exception as e:
        print(f"\n❌ Nepodarilo sa načítať objednaný obed. (Detail: {e})")
        import traceback
        traceback.print_exc()
        return

def main():
    parser = argparse.ArgumentParser(description='EduPage Monitor')
    parser.add_argument('--date', type=str, help='Dátum vo formáte DD.MM.YYYY (napr. 20.02.2026)')
    parser.add_argument('--lunch', action='store_true', help='Zobraziť objednaný obed pre daný dátum (použi --date na zadanie dátumu)')
    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, '%d.%m.%Y').date()
        except ValueError:
            print(f"Chyba: Neplatný formát dátumu '{args.date}'. Použite DD.MM.YYYY.")
            return

    # Automaticky hľadá .env v pracovnom adresári alebo v ceste skriptu
    load_dotenv(override=True)

    try:
        username, password = get_credentials()
    except ValueError as e:
        print(e)
        return

    subdomains_env = os.getenv("SUBDOMAINS", "")
    if not subdomains_env:
        print("Chýba premenná SUBDOMAINS v .env súbore.")
        return
        
    subdomains = [s.strip() for s in subdomains_env.split(",") if s.strip()]
    
    for sub in subdomains:
        print(f"\n{'='*60}")
        print(f"ŠKOLA: {sub.upper():<51} =")
        print(f"{'='*60}")
        
        try:
            edupage = Edupage()
            edupage.login(username, password, sub)
            
            child_ids = []
            if "parentStudentids" in edupage.data:
                child_ids = edupage.data["parentStudentids"]
            elif "children" in edupage.data:
                child_ids = list(edupage.data["children"].keys())
            
            if not child_ids:
                print(f"Zpracovávam priamy profil...")
                show_timetable(edupage, target_date=target_date)
                show_grades(edupage)
                show_notifications(edupage)
            else:
                original_userid = edupage.get_user_id()
                for cid in child_ids:
                    child_name = DbiHelper(edupage).fetch_student_name(cid)
                    if not child_name:
                         if "children" in edupage.data and str(cid) in edupage.data["children"]:
                             child_name = edupage.data["children"][str(cid)].get("meno", "Neznáme meno")
                         else:
                             child_name = f"Dieťa ID: {cid}"

                    print(f"\n>>> DIEŤA: {child_name} <<<")
                    
                    try:
                        edupage.switch_to_child(int(cid))
                        edupage.data['userid'] = str(cid)
                        
                        # Ak je zadaný --lunch, zobrazíme iba obed
                        if args.lunch:
                            if not args.date:
                                print("Chyba: Dátum potrebný pri použití --lunch. Použite: --lunch --date DD.MM.YYYY")
                                continue
                            show_my_lunch(edupage, cid, target_date)
                        else:
                            # Bez --lunch zobrazíme rozvrh, známky a oznamy
                            show_timetable(edupage, student_id=cid, target_date=target_date)
                            show_grades(edupage)
                            show_notifications(edupage)
                    except Exception as child_e:
                        print(f"Chyba pri dieťati {cid}: {child_e}")
                    finally:
                        try:
                            edupage.switch_to_parent()
                            edupage.data['userid'] = original_userid
                        except:
                            pass
            
        except Exception as e:
            print(f"Chyba pri škole {sub}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
