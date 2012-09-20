# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IndexEntry'
        db.create_table('smartlinks_indexentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=300, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('smartlinks', ['IndexEntry'])

        # Adding unique constraint on 'IndexEntry', fields ['value', 'content_type', 'object_id']
        db.create_unique('smartlinks_indexentry', ['value', 'content_type_id', 'object_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'IndexEntry', fields ['value', 'content_type', 'object_id']
        db.delete_unique('smartlinks_indexentry', ['value', 'content_type_id', 'object_id'])

        # Deleting model 'IndexEntry'
        db.delete_table('smartlinks_indexentry')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'smartlinks.indexentry': {
            'Meta': {'unique_together': "(('value', 'content_type', 'object_id'),)", 'object_name': 'IndexEntry'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_index': 'True'})
        }
    }

    complete_apps = ['smartlinks']