class Model:
    def __init__(self, db):
        self.db = db

    def query_function_parameters(self, fnname):
        cur = self.db.cursor()
        cur.execute("""
            select Ty.param, Ty.value, Doc.value from
            ( select Value, param
              from Params_extra
              where Anname == 'param_order' AND fnname == :fnname
            ) as Ord

            inner join
            ( select param, value
              from params_extra
              where anname == 'param_type' and fnname == :fnname
            ) as Ty on Ty.param == Ord.param

            left outer join
            ( select param, value from parameters
              where fnname == :fnname
            ) as Doc on Doc.param == Ord.param

            order by Ord.value
        """, { "fnname": fnname })
        for name, ty, doc in cur:
            yield { "name": name, "type": ty, "doc": doc }
        cur.close()

    def query_annotations(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select anname, value
            from annotations
            where fnname == ? and anname not in ('type', 'start-line', 'end-line')
            -- we rely on sqlite here to get the annotations in order as they
            -- are in the docstring, because we insert them in that order.
            order by rowid
        """, (entity, ))
        for name, value in cur:
            yield { "name": name, "value": value }
        cur.close()

    def query_line_number(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from annotations
            where fnname == ? and anname == 'start-line'
        """, (entity,))
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_type(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from annotations
            where fnname == ? and anname == 'type'
        """, [entity])
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_git_commit(self):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from metadata
            where key = 'git-commit'
        """)
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_bj_globals(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='global'
                AND fnname LIKE 'bj_%'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_cj_globals(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='global'
                AND fnname NOT LIKE 'bj_%'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_natives(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='native'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_functions(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='function'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_types(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='type'
        """)
        return list(x[0] for x in cur.fetchall())

