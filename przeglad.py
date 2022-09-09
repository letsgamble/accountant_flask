from app import manager


@manager.assign("przeglad")
def przeglad(manager):
    print(f'\n********** PRZEGLAD ***********')
    print("Account balance:", manager.stan_konta)
    print(f"Warehouse: {manager.new_magazyn}\n")


manager.json_file_loader()
manager.json_file_handler()
manager.execute("przeglad")
# manager.json_file_saver()
