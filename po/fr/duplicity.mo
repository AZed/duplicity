��    }        �   �      �
  (   �
  "   �
  /   �
  3     +   9  ;   e  %   �  `   �     (     8     Q     c     w     �  7   �     �     �     �       �   3  ;   �  1     C   9  )   }     �  /   �     �  ;     6   ?  �   v  d   �  4   c     �  B   �     �  Y        h  9   ~  H   �            d     +   �  ;   �     �  .   �     #     :  0   V  ;   �     �  _   �  -   5  6   c  -   �  *   �  ,   �  ^      .        �  #   �  '   �       �   !     �  g   v     �  5   �  ?   ,  V   l     �  3   �  5     /   G  1   w  4   �  #   �  E        H  %   N     t  !   �     �     �     �     �          $  #   =  G   a  I   �  ;   �  x   /  f   �  z     �   �  9     J   G     �     �     �  <   �     �                       
   )     4     A     S     s     y     �     �     �     �  4   �  *   �                    !   9      [   �  `   1   /"  )   a"  B   �"  T   �"  E   ##  M   i#  -   �#  �   �#     �$  *   �$     �$     �$     %      %  @   >%     %  !   �%  "   �%      �%  �   �%  \   �&  B   '  [   Z'  B   �'  *   �'  H   $(     m(  F   �(  M   �(  �   )  �   �)  Q   R*  *   �*  p   �*  !   @+  e   b+     �+  V   �+  y   7,  
   �,      �,  �   �,  =   f-  R   �-     �-  B   .  *   H.  1   s.  e   �.  f   /     r/  �   �/  M   !0  S   o0  =   �0  O   1  B   Q1  v   �1  P   2     \2  +   q2  .   �2  #   �2    �2  �   4  �   �4  $   G5  O   l5  R   �5  x   6     �6  a   �6  B   
7  B   M7  T   �7  P   �7  6   68  Z   m8     �8  &   �8     �8  F   9  6   [9  #   �9  (   �9  ,   �9  &   :  "   3:  5   V:  c   �:  j   �:  R   [;  �   �;  �   Z<  �   �<  �   �=  C   N>  V   �>     �>     �>     ?  U   ?     k?     z?     �?     �?     �?     �?     �?     �?  )   �?     !@     '@     .@     6@     =@     T@  A   \@  <   �@     �@     �@     �@  /   A     =A        !   W      1   	           .       I       o   A          N       {   7   n   (   t       y   d       w   X              q              ?       )       "   v           [       Y      *             \   '      K      F   C   
   +       ;       $       u   ,   #   :           R      ^          <   T   H   2   =   9      g   l       3      r       D   p              M       P   j   @       %   _   5   }       &   S   E   4   f       a   Z   J   /          z   |       O                  0           b       Q   e      s   B                     -   i            `       k      >   ]   U   G       V       L   8   x   h   6   c   m    %d difference found %d differences found %d file compared %d files compared %d file exists in cache %d files exist in cache %d file exists on backend %d files exist on backend %s not found in archive, no files restored. Added incremental Backupset (start_time: %s / end_time: %s) Added set %s to pre-existing chain %s Also found %d backup set not part of any chain, Also found %d backup sets not part of any chain, Archive dir: %s Backend error detail: %s Backup Statistics Calculated hash: %s Chain end time:  Chain start time:  Cleaning up previous partial %s backup set, restarting. Collection Status Command line error: %s Connecting with backend: %s Copying %s to local cache. Current active backup chain is older than specified time.  However, it will not be deleted.  To remove all your backups, manually purge the repository. Deleting backup set at time: Deleting backup sets at times: Deleting local %s (not authoritative at backend). Deleting this file from backend: Deleting these files from backend: Enter 'duplicity --help' for help screen. Error opening file %s Extracting backup chains from list of files: %s Failed to read %s: %s Fatal Error: Neither remote nor local manifest is readable. Fatal Error: No manifests found for most recent backup Fatal Error: Remote manifest does not match local one.  Either the remote backup set or the local archive directory has been corrupted. Fatal Error: Unable to start incremental backup.  Old signatures not found and incremental specified File %s is not part of a known set; creating new set File %s is part of known set Found %d secondary backup chain. Found %d secondary backup chains. Found backup chain %s Found old backup set at the following time: Found old backup sets at the following times: Found orphaned set %s Found primary backup chain with matching signature chain: Found the following file to delete: Found the following files to delete: Full GPG error detail: %s Giving up trying to execute '%s' after %d attempt Giving up trying to execute '%s' after %d attempts Ignoring file (rejected by backup set) '%s' Ignoring incremental Backupset (start_time: %s; needed: %s) Incremental Last %s backup left a partial set, restarting. Last full backup date: Last full backup date: none Last full backup is too old, forcing full backup Local and Remote metadata are synchronized, no sync needed. Manifest hash: %s Max open files of %s is too low, should be >= 1024.
Use 'ulimit -n 1024' or higher to correct.
 No backup chains with active signatures found No extraneous files found, nothing deleted in cleanup. No files found in archive - nothing restored. No old backup sets found, nothing deleted. No orphaned or incomplete backup sets found. No signature chain for the requested time.  Using oldest available chain, starting at time %s. No signatures found, switching to full backup. Num volumes: Number of contained backup sets: %d Preferring Backupset over previous one! Processed volume %d of %d RESTART: Impossible backup state: manifest has %d vols, remote has %d vols.
         Restart is impossible ... duplicity will clean off the last partial
         backup then restart the backup from the beginning. RESTART: The first volume failed to upload before termination.
         Restart is impossible...starting backup from beginning. RESTART: Volumes %d to %d failed to upload before termination.
         Restarting backup at volume %d. Reading results of '%s' Rerun command with --force option to actually delete. Run duplicity again with the --force option to actually delete. Running in 'ignore errors' mode due to %s; please re-consider if this was not intended Secondary chain %d of %d: Sync would copy the following from remote to local: Sync would remove the following spurious local files: Synchronizing remote metadata to local cache... Temp has %d available, backup will use approx %d. Temp space has %d available, backup needs approx %d. There are backup set(s) at time(s): These may be deleted by running duplicity with the "cleanup" command. Time: Total number of contained volumes: %d Type of backup set: Unable to get free space on temp. Unable to get max open files. Unable to load gio module User error detail: %s Using archive dir: %s Using backup name: %s Verify complete: %s, %s. Volume was signed by key %s, not %s Warning, discarding last backup set, because of missing signature file. Warning, found incomplete backup sets, probably left from aborted session Warning, found signatures but no corresponding backup files Warning, found the following local orphaned signature file: Warning, found the following local orphaned signature files: Warning, found the following orphaned backup file: Warning, found the following orphaned backup files: Warning, found the following remote orphaned signature file: Warning, found the following remote orphaned signature files: Warning: Option %s is pending deprecation and will be removed in a future release.
Use of default filenames is strongly suggested. Which can't be deleted because newer sets depend on them. a previously scheduled task has failed; propagating the result immediately absolute_path active workers = %d alias and %d incomplete backup set. and %d incomplete backup sets. backup name char command file_descriptor filename gpg-key-id imap_mailbox inserting barrier instantiating at concurrency %d local number options path regular_expression remote running task synchronously (asynchronicity disabled) scheduling task for asynchronous execution seconds shell_pattern task completed successfully task execution done (success: %s) time Project-Id-Version: duplicity
Report-Msgid-Bugs-To: FULL NAME <EMAIL@ADDRESS>
POT-Creation-Date: 2011-10-10 16:25-0500
PO-Revision-Date: 2010-05-23 16:47+0000
Last-Translator: Kenneth Loafman <kenneth@loafman.com>
Language-Team: French <fr@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=n > 1;
X-Launchpad-Export-Date: 2011-10-11 05:36+0000
X-Generator: Launchpad (build 14123)
 %d différence trouvée %d différences trouvées %d fichier comparé %d fichiers comparés %d fichier existe dans le cache %d fichiers existent dans le cache %d fichier existe sur le serveur central %d fichiers existent sur le serveur central %s n’a pas été trouvé dans l’archive, aucun fichier restauré. Jeu de sauvegarde incrémentale ajouté (date_début : %s ; date_fin : %s) Jeu %s ajouté à la chaîne préexistante %s %d jeu de sauvegarde ne faisant partie d’aucune chaîne a été aussi trouvé, %d jeux de sauvegarde ne faisant partie d’aucune chaîne ont été aussi trouvés, Dossier d’archive : %s Détails de l’erreur de sauvegarde : %s Statistiques de sauvegarde Empreinte calculée : %s Date de fin de chaîne :  Date de début de chaîne :  Nettoyage du dernier jeu partiel de sauvegarde %s, redémarrage. État de la collection Erreur de ligne de commande : %s Connexion au serveur central : %s Copie de %s vers le cache local. La chaîne de sauvegarde active actuelle est plus ancienne que la date indiquée. Cependant elle ne sera pas supprimée. Pour ôter toutes vos sauvegardes, purgez manuellement leur dépôt. Suppression du jeu de sauvegarde daté du : Suppression des jeux de sauvegarde datés du : Supprime le %s local (ne fait pas autorité au niveau du serveur). Supprimer ce fichier de l’arrière plan : Supprimer ces fichiers de l’arrière plan : Entrez « duplicity --help » pour afficher l’écran d’aide. Erreur lors de l’ouverture du fichier %s Extraction des chaînes de sauvegarde depuis la liste des fichiers : %s Impossible de lire %s : %s Erreur fatale : ni le manifeste local, ni le distant n’est lisible. Erreur fatale : aucun manifeste présent pour la sauvegarde la plus récente Erreur fatale : le manifeste distant ne correspond pas à celui en local. Soit le jeu de sauvegarde distant, soit le dossier local d’archive a été corrompu. Erreur fatale : impossible de démarrer la sauvegarde incrémentale, anciennes signatures non trouvées pour la méthode incrémentale indiquée Le fichier %s ne fait pas partie d’un jeu connu ; création d’un nouveau jeu Le fichier %s fait partie d’un jeu connu %d chaîne secondaire de sauvegarde a été trouvée. %d chaînes secondaires de sauvegarde ont été trouvées. Chaîne de sauvegarde %s trouvée Ancien jeu de sauvegarde trouvé à la date du : Anciens jeux de sauvegarde trouvés aux dates du : Jeu orphelin %s trouvé Chaîne primaire de sauvegarde trouvée avec la signature de chaîne correspondante : Le fichier suivant a été trouvé pour la suppression : Les fichiers suivants ont été trouvés pour la suppression : Intégrale Détails de l’erreur GPG : %s Abandon des essais d’exécution de « %s » après %d tentative Abandon des essais d’exécution de « %s » après %d tentatives Fichier ignoré (rejeté par le jeu de sauvegarde) « %s » Ignore le jeu de sauvegarde incrémentale (date_début : %s ; nécessaire : %s) Incrémentale La dernière sauvegarde %s a laissé un jeu partiel, redémarrage. Date de dernière sauvegarde intégrale : Date de dernière sauvegarde intégrale : aucune La dernière sauvegarde intégrale est trop ancienne, forçage d’une nouvelle sauvegarde intégrale Les métadonnées locales et distantes sont déjà synchronisées. Aucune synchronisation nécessaire. Empreinte manifeste : %s Le nombre maximum de fichiers ouverts pour %s est trop bas, il devrait être >= 1024.
Utilisez « ulimit -n 1024 » (ou supérieur) pour corriger.
 Aucune chaîne de sauvegarde avec les signatures actives n’a été trouvée Aucun fichier étranger détecté, aucune suppression effectuée lors du nettoyage. Aucun fichier trouvé dans l’archive – rien à restaurer. Aucun ancien jeu de sauvegarde n’a été trouvé, rien n’a été supprimé. Aucun jeu orphelin ou incomplet de sauvegarde n’a été trouvé. Aucune chaîne de signatures pour la date indiquée. Utilise la chaîne disponible la plus ancienne, à compter du %s. Aucune signature de sauvegarde trouvée, bascule vers une sauvegarde intégrale. Nombre de volumes : Nombre de jeux de sauvegarde contenus : %d Jeu de sauvegarde préféré au précédent ! Le volume %d sur %d a été traité REDÉMARRAGE : état de sauvegarde impossible :
              le manifeste indique %d volumes, le distant en a %d.
              Redémarrage impossible... duplicity va nettoyer la dernière
              sauvegarde partielle puis reprendre la sauvegarde depuis le début. REDÉMARRAGE : échec de téléchargement du premier volume avant le délai de fin.
              Le redémarrage est impossible... lancement de la sauvegarde depuis le début. REDÉMARRAGE : échec de téléchargement de %d volumes sur %d avant le délai de fin.
              Redémarrage de la sauvegarde au volume %d. Lecture des résultats de « %s » Veuillez relancer la commande avec l'option --force pour forcer la suppression. Exécutez duplicity à nouveau avec l’option --force pour supprimer réellement. Exécution en mode « ignorer les erreurs » à cause de %s ; veuillez reconsidérer si ceci n’était pas souhaité Chaîne secondaire %d sur %d : La synchronisation va copier localement les éléments suivants à partir de l’hôte distant : La synchronisation va supprimer les fichiers parasites suivants : Synchronisation des métadonnées distantes vers le cache local... Il y a %d d’espace temporaire disponible, la sauvegarde va nécessiter environ %d. Il y a %d d’espace temporaire disponible, la sauvegarde nécessite environ %d. Il y a un ou plusieurs jeux de sauvegarde datés du : Ceux-ci peuvent être supprimés en exécutant duplicity avec la commande « cleanup ». Date : Nombre total de volumes contenus : %d Type de jeu de sauvegarde : Impossible de déterminer l’espace libre dans le dossier temporaire. Impossible d’obtenir le maximum de fichiers ouverts. Impossible de charger le module gio Détails de l’erreur utilisateur : %s Utilisation du répertoire d’archive : %s Utilisation du nom de sauvegarde : %s Vérification complète : %s, %s. Le volume a été signé par la clé %s et non pas %s Avertissement, rejet du dernier jeu de sauvegarde à cause de l’absence du fichier de signatures. Avertissement, jeux de sauvegarde incomplets trouvés, probablement laissés par des sessions interrompues Avertissement, signatures trouvées mais aucun fichier de sauvegarde correspondant Avertissement, le fichier orphelin local suivant de signatures a été trouvé : Avertissement, les fichiers orphelins locaux suivants de signatures ont été trouvés : Avertissement, le fichier orphelin suivant de sauvegarde a été trouvé : Avertissement, les fichiers orphelins suivants de sauvegarde ont été trouvés : Avertissement, le fichier orphelin distant suivant de signatures a été trouvé : Avertissement, les fichiers orphelins distants suivants de signatures ont été trouvés : Avertissement : l’option %s est obsolescente et sera retirée dans une version future.
L’utilisation des noms de fichiers par défaut est fortement suggérée. Qui ne peuvent être supprimés car de nouveaux jeux en dépendent. une tâche planifiée précédemment a échoué ; propagation immédiate du résultat chemin_absolu exécutants actifs = %d alias ainsi que %d jeu incomplet de sauvegarde. ainsi que %d jeux incomplets de sauvegarde. nom_sauvegarde caract. commande descripteur_fichier nom_de_fichier identifiant_clé_gpg boîte_aux_lettres_IMAP insertion d’une barrière instanciation au niveau de concurrence %d local nombre options chemin expression_régulière distant exécution synchronisée de la tâche (asynchronisme désactivé) planification d’une tâche exécutée de façon asynchrone secondes motif_shell tâche achevée avec succès exécution de tâche réalisée (succès : %s) temps 