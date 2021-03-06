# Copyright 2020 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import psycopg2
from ebi_eva_common_pyutils.pg_utils import get_result_cursor, get_all_results_for_query


def get_db_conn_for_species(species_db_info):
    db_name = "dbsnp_{0}".format(species_db_info["dbsnp_build"])
    pg_conn = psycopg2.connect("dbname='{0}' user='{1}' host='{2}'  port={3}".
                               format(db_name, "dbsnp", species_db_info["pg_host"], species_db_info["pg_port"]))
    return pg_conn


def get_species_info(metadata_connection_handle, dbsnp_species_name="all"):
    get_species_info_query = "select distinct database_name, scientific_name, dbsnp_build, pg_host, pg_port from " \
                             "dbsnp_ensembl_species.import_progress a " \
                             "join dbsnp_ensembl_species.dbsnp_build_instance b " \
                                "on b.dbsnp_build = a.ebi_pg_dbsnp_build "
    if dbsnp_species_name != "all":
        get_species_info_query += "where database_name = '{0}' ".format(dbsnp_species_name)
    get_species_info_query += "order by database_name"

    pg_cursor = get_result_cursor(metadata_connection_handle, get_species_info_query)
    species_set = [{"database_name": result[0], "scientific_name": result[1], "dbsnp_build":result[2],
                    "pg_host":result[3], "pg_port":result[4]}
                   for result in pg_cursor.fetchall()]
    pg_cursor.close()
    return species_set


# Get connection information for each Postgres instance of the dbSNP mirror
def get_dbsnp_mirror_db_info(pg_metadata_dbname, pg_metadata_user, pg_metadata_host):
    with psycopg2.connect("dbname='{0}' user='{1}' host='{2}'".format(pg_metadata_dbname, pg_metadata_user,
                                                                      pg_metadata_host)) as pg_conn:
        dbsnp_mirror_db_info_query = "select * from dbsnp_ensembl_species.dbsnp_build_instance"
        dbsnp_mirror_db_info = [{"dbsnp_build": result[0], "pg_host": result[1], "pg_port": result[2]}
                                for result in get_all_results_for_query(pg_conn, dbsnp_mirror_db_info_query)]
    return dbsnp_mirror_db_info


def get_variant_warehouse_db_name_from_assembly_and_taxonomy(metadata_connection_handle, assembly, taxonomy):
    query = f"select t.taxonomy_code, a.assembly_code " \
            f"from assembly a " \
            f"left join taxonomy t on (t.taxonomy_id = a.taxonomy_id) " \
            f"where a.assembly_accession = '{assembly}'" \
            f"and a.taxonomy_id = {taxonomy}"
    rows = get_all_results_for_query(metadata_connection_handle, query)
    if len(rows) == 0:
        return None
    elif len(rows) > 1:
        options = ', '.join((f'{r[0]}_{r[1]}' for r in rows))
        raise ValueError(f'More than one possible database for assembly {assembly} and taxonomy {taxonomy} found: '
                         f'{options}')
    database_name = f'eva_{rows[0][0]}_{rows[0][1]}'
    return database_name
