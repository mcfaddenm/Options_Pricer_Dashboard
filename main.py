from basics import *

if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 300)
    bal = updateBal()

    quotes = getWLquotes()
    print(quotes)