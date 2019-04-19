### Translate
Inkcut currently support English and French languages. You can easily translate it.

#### Generate language file
To generate language 'ts' file, you need to run this lupdate-qt5 command replacing fr_FR by the language you want to add.
```bash
lupdate-qt5 inkcut/*/*.enaml -I inkcut/*/*/*.enaml -ts translations/fr_FR.ts
```

#### Translate
The generated ts file can be translated using Qt5 linguistic application

#### Prepare files for release
Before release a new version, or in order to test your translation you need to execute the following command :

```bash
lrelease-qt5 translations/*.ts
```

This will generate the necessary qm file that will be used by Inkcut
