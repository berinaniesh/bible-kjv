#!/bin/bash

psql -c "DROP DATABASE bibledev2;"
psql -c "CREATE DATABASE bibledev2;"
psql -d bibledev2 < bible.sql
