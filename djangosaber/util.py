
def key(table, id='', relation=''):
    # #logging.debug("key: {} {} {}".format(table, id, relation))
    return ('%s.%s.%s'%(table, id, relation)).rstrip('.')
