from datamodel.mongoDB_query import MongoDB


def AuthDB(account, password):
    dbinstance = MongoDB("elle")
    query = {"username": account}

    ret = dbinstance.get_single_data("account",query)

    if(ret is None):
        return 1  # user not found
    if(ret.get('password') != password):
        return 2  # password not match
    return 0 #success

